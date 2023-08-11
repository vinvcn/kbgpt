import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Type

from sanic import Sanic
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    and_,
)

from config import profile
from kbgpt.api.libs.resources import LifeCycleMixin
from kbgpt.lib.db.mysql import Base, Crud
from kbgpt.lib.utils import load_config


class TaskStatus(Enum):
    """task status enum"""

    RUNNING = 0
    SUCCESS = 1
    FAIL = 2


class TaskMutExclusive(Enum):
    """task mutual exlusive enum"""

    TASK_ID = 0
    NAME = 1


class TaskRecord(Base):
    __tablename__ = "task_task_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    task_name = Column(String(100, collation="utf8mb4_unicode_ci"))
    task_handle = Column(String(200, collation="utf8mb4_unicode_ci"))
    parameters = Column(Text(collation="utf8mb4_unicode_ci"))
    fire_immediate = Column(Boolean, default=False)
    max_attempt = Column(Integer, default=4)
    next_execution_time = Column(DateTime, default=datetime.utcnow)
    attempt = Column(Integer, default=0)
    exclusive = Column(Integer, default=0)
    status = Column(Integer, default=0)  # 0 not complete, 1 successfull, 2 failed
    error = Column(String(200, collation="utf8mb4_unicode_ci"))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (UniqueConstraint("task_id", name="uq_mytable_columns"),)


class AttemptConfigRecord(Base):
    __tablename__ = "task_attempt_config_record"

    attempt = Column(Integer, primary_key=True)
    delay = Column(Integer)


class FuncWrapper:
    def __init__(self, name: str, handle: str):
        self.name = name
        self.handle = handle

    async def __call__(self, *args: Any, app: Sanic, record: TaskRecord, **kwds: Any):
        pass


class Task:
    @property
    def name(self):
        return self.__class__.__name__

    @property
    def handle(self):
        return self.__class__.__name__

    @property
    def done(self):
        return self.future.done()

    @property
    def cancelled(self):
        return self.future.cancelled()

    @property
    def task_id(self):
        return self.record.task_id

    @property
    def mut_exclusive(self):
        return self.record.exclusive

    def is_conflict(self, other: "Task"):
        if self is other:
            return True
        if self.task_id == other.task_id:
            return True
        if self.mut_exclusive is TaskMutExclusive.NAME and self.name == other.name:
            return True
        if self.task_id is TaskMutExclusive.TASK_ID and self.task_id == other.task_id:
            return True
        return False

    def __init__(self, record: TaskRecord = None, afunc: FuncWrapper = None):
        self.record = record
        self.future: asyncio.Task = None
        self.afunc = afunc

    async def __call__(self, *args: Any, **kwargs) -> Any:
        await self.afunc(*args, **kwargs)


class TaskManager(LifeCycleMixin):
    def __init__(self, app: Sanic, crud: Crud) -> None:
        self.app = app
        self.crud = crud
        self.mapping: Dict[str, Type[FuncWrapper]] = dict()
        self.active_task: List[Task] = []

    async def init(self, app: Sanic):
        configs = [
            AttemptConfigRecord(**con)
            for con in load_config(__file__)[profile.name.lower()]
        ]
        self.crud.truncate_table(AttemptConfigRecord.__tablename__)
        self.crud.batch_insert(configs)

    async def destroy(self, app: Sanic):
        for tsk in self.active_task:
            tsk.future.cancel()

    async def get_task(self, name: str, task_id: str) -> TaskRecord:
        params = {}
        if name:
            params["task_name"] = name
        if task_id:
            params["task_id"] = task_id
        return self.crud.get_first_by(
            TaskRecord, filter_params=params, order_col="created_at"
        )

    async def set_task_status(self, name: str, task_id: str, status: TaskStatus):
        record = await self.get_task(name, task_id)
        record.status = status.value
        self.crud.update_rows(record.__class__, [record])

    def register_task_name_handle(self, afunc: Type[FuncWrapper], handle: str):
        self.mapping[handle] = afunc(handle, handle)

    async def get_retry_config(self):
        results = self.crud.get_all(AttemptConfigRecord)
        return {a_conf.attempt: a_conf.delay for a_conf in results}

    async def add_task(self, record: TaskRecord):
        self.crud.batch_insert([record])

    async def _fire_task(self, new_task: Task):
        # decide if it's ok to start the task
        if not any([new_task.is_conflict(other) for other in self.active_task]):
            new_task.future = asyncio.ensure_future(
                new_task(app=self.app, record=new_task.record)
            )
            logging.info(
                "fire task %s in the %d attempt", new_task.name, new_task.record.attempt
            )
            self.active_task.append(new_task)

    async def _maintain_active(self):
        """maintain active tasks"""
        done_tasks = [t for t in self.active_task if t.done]
        retries = await self.get_retry_config()
        for task in done_tasks:
            # update db for all done tasks
            record = task.record
            exc = task.future.exception()
            if exc is not None:
                logging.error(
                    "task %s failed at attempt %d due to exception %s",
                    task.name,
                    record.attempt,
                    exc,
                )
                record.attempt += 1
                if record.attempt > record.max_attempt:
                    record.completed_at = datetime.utcnow()
                    record.status = TaskStatus.FAIL.value
                    record.error = repr(exc)[:200]
                    logging.warning(
                        "task %s has exceeded max attempt of %d, set it to status %s",
                        task.name,
                        record.max_attempt,
                        TaskStatus.FAIL.name,
                    )
                else:
                    # schedule for next run
                    record.next_execution_time += timedelta(
                        seconds=retries[record.attempt]
                    )
                    logging.info(
                        "task %s scheduled at time %s as attempt %d",
                        task.name,
                        record.next_execution_time,
                        record.attempt,
                    )
            else:
                # mark all done tasks without exception to be success
                record.status = TaskStatus.SUCCESS.value
                record.completed_at = datetime.utcnow()
                logging.info("task %s was done mark it to %s", task.name, record.status)

            self.crud.update_rows(record.__class__, [record])
        # filter out all done and cancelled tasks
        self.active_task = [t for t in self.active_task if not (t.done or t.cancelled)]

    async def schedule(self):
        while True:
            try:
                await asyncio.sleep(10)
                await self._maintain_active()
                results = self.crud.get_all(
                    TaskRecord,
                    the_filter=and_(
                        TaskRecord.status == TaskStatus.RUNNING.value,
                        TaskRecord.attempt <= TaskRecord.max_attempt,
                    ),
                )
                for task in results:
                    tsk: TaskRecord = task
                    if tsk.next_execution_time <= datetime.now():
                        # if task is due, create task
                        afunc = self.mapping[tsk.task_handle]
                        new_task = Task(record=tsk, afunc=afunc)
                        await self._fire_task(new_task)
            except Exception as e:
                logging.exception(e)

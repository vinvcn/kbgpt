import asyncio
import json
import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Type
from uuid import uuid4

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
    RUNNING = 0
    SUCCESS = 1
    FAIL = 2


class TaskMutExclusive(Enum):
    NAME = 0
    TASK_ID = 1


class AttemptStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    FAIL = 2


class TaskRecord(Base):
    __tablename__ = "task_task_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    task_name = Column(String(100, collation="utf8mb4_unicode_ci"))
    task_handle = Column(String(200, collation="utf8mb4_unicode_ci"))
    parameters = Column(Text(collation="utf8mb4_unicode_ci"))
    fire_immediate = Column(Boolean, default=False)
    max_attempt = Column(Integer, default=4)
    status = Column(Integer, default=0)  # 0 not complete, 1 successfull, 2 failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (UniqueConstraint("task_id", name="uq_mytable_columns"),)


class AttemptRecord(Base):
    __tablename__ = "task_attempt_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    next_execution_time = Column(DateTime, default=datetime.utcnow)
    attempt = Column(Integer, default=0)
    status = Column(Integer, default=0)  # 0 not complete, 1 successfull, 2 failed
    created_at = Column(DateTime, default=datetime.utcnow)


class AttemptConfigRecord(Base):
    __tablename__ = "task_attempt_config_record"

    attempt = Column(Integer, primary_key=True)
    delay = Column(Integer)


# class TaskModel(BaseModel):
#     task_id: str
#     status: int
#     created_at: datetime


# class ExecutionModel(BaseModel):
#     task_id: str
#     execution_time: datetime
#     created_ata: datetime


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

    def __init__(
        self,
        task_id: str,
        params: Any,
        fire_immediate: bool = False,
        orm_task: TaskRecord = None,
        orm_attempt: AttemptRecord = None,
        mut_exclusive: TaskMutExclusive = TaskMutExclusive.TASK_ID,
    ):
        self.task_id = task_id
        if isinstance(params, str):
            self.params = self.deserialize_params(params)
        else:
            self.params = params
        self.fire_immediate = fire_immediate
        self.orm_task = orm_task
        self.orm_attempt = orm_attempt
        self.future: asyncio.Task = None
        self.mut_exclusive = mut_exclusive

    def to_orm(self):
        task = TaskRecord(
            task_id=self.task_id,
            task_name=self.name,
            task_handle=self.handle,
            parameters=self.serialize_params(),
            fire_immediate=self.fire_immediate,
        )
        attempt = AttemptRecord(task_id=task.task_id)
        return task, attempt

    def serialize_params(self):
        return json.dumps(self.params)

    def deserialize_params(self, params):
        return json.loads(params)

    async def __call__(self, *args: Any, app: Sanic, **kwds: Any) -> Any:
        pass


class TaskManager(LifeCycleMixin):
    def __init__(self, app: Sanic, crud: Crud) -> None:
        self.app = app
        self.crud = crud
        self.mapping: Dict[str, Type[Task]] = dict()
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

    async def get_task(self, name: str, task_id: str):
        params = {}
        if name:
            params["task_name"] = name
        if task_id:
            params["task_id"] = task_id
        return self.crud.get_first_by(
            TaskRecord, filter_params=params, order_col="created_at"
        )

    def register_task_name_handle(self, task_cls: Type[Task]):
        self.mapping[task_cls.__name__] = task_cls

    async def get_retry_config(self):
        results = self.crud.session.query(AttemptConfigRecord).all()
        return {a_conf.attempt: a_conf.delay for a_conf in results}

    async def add_task(self, new_task: Task) -> Task:
        task, attempt = new_task.to_orm()
        self.crud.batch_insert([task, attempt])

    async def _fire_task(
        self, orm_task: TaskRecord, orm_attempt: AttemptRecord, new_task: Task
    ):
        # decide if it's ok to start the task
        if not any([new_task.is_conflict(other) for other in self.active_task]):
            new_task.future = asyncio.ensure_future(
                new_task(app=self.app, record=orm_task)
            )
            logging.info(
                "fire task %s in the %d attempt",
                new_task.name,
                orm_attempt.attempt,
            )
            self.active_task.append(new_task)

    async def _maintain_active(self):
        """maintain active tasks"""
        done_tasks = [t for t in self.active_task if t.done]
        retries = await self.get_retry_config()
        for task in done_tasks:
            # update db for all done tasks
            att = task.orm_attempt
            tsk = task.orm_task
            exc = task.future.exception()
            if exc is not None:
                logging.error(
                    "task %s failed at attempt %d due to exception %s",
                    task.name,
                    att.attempt,
                    exc,
                )
                att.attempt += 1
                if att.attempt > tsk.max_attempt:
                    tsk.status = TaskStatus.FAIL.value
                    tsk.completed_at = datetime.utcnow()
                    att.status = AttemptStatus.FAIL.value
                    logging.warning(
                        "task %s has exceeded max attempt of %d, set it to status %s",
                        task.name,
                        tsk.max_attempt,
                        AttemptStatus.FAIL.name,
                    )
                else:
                    # schedule for next run
                    att.next_execution_time += timedelta(seconds=retries[att.attempt])
                    logging.info(
                        "task %s scheduled at time %s as attempt %d",
                        task.name,
                        att.next_execution_time,
                        att.attempt,
                    )
            else:
                # mark all done tasks without exception to be success
                att.status = AttemptStatus.SUCCESS.value
                tsk.status = TaskStatus.SUCCESS.value
                logging.info("task %s was done mark it to %s", task.name, att.status)

            self.crud.session.add(att)
            self.crud.session.add(tsk)
        # filter out all done and cancelled tasks
        self.active_task = [t for t in self.active_task if not (t.done or t.cancelled)]

    async def schedule(self):
        while True:
            try:
                await asyncio.sleep(10)
                await self._maintain_active()

                query = (
                    self.crud.session.query(AttemptRecord, TaskRecord)
                    .join(TaskRecord, AttemptRecord.task_id == TaskRecord.task_id)
                    .filter(
                        and_(
                            AttemptRecord.status == AttemptStatus.PENDING.value,
                            AttemptRecord.attempt <= TaskRecord.max_attempt,
                        )
                    )
                )

                results = query.all()

                for attempt, task in results:
                    att: AttemptRecord = attempt
                    tsk: TaskRecord = task

                    if att.next_execution_time <= datetime.now():
                        # if task is due, create task
                        task_cls = self.mapping[tsk.task_handle]
                        new_task = task_cls(
                            task_id=tsk.task_id,
                            params=tsk.parameters,
                            orm_task=tsk,
                            orm_attempt=att,
                        )
                        await self._fire_task(tsk, att, new_task)

            except Exception as e:
                logging.exception(e)

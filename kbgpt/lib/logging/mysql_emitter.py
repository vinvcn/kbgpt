"""
mysql emitter
"""
import asyncio
from asyncio.queues import Queue
from typing import Any, List

from sanic import Sanic
from sqlalchemy.exc import SQLAlchemyError

from kbgpt.api.libs.resources import LifeCycleMixin
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.logging.emitter import Emitter


class MySqlEmitter(Emitter, LifeCycleMixin):
    """
    Emits to MySql
    """

    def __init__(self, crud: Crud) -> None:
        super().__init__()
        self.crud = crud
        self.queue = Queue(0)

    async def init(self, app: Sanic):
        pass

    async def destroy(self, app: Sanic):
        events = await self.dequeue()
        self.crud.batch_insert(events)
        await self.queue.join()

    async def aemit(self, events: List[Any] | Any = None):
        if not events:
            return
        if not isinstance(events, list):
            events = [events]
        for e in events:
            await self.queue.put(e)

    async def dequeue(self) -> List[Any]:
        """
        get all events out of queue
        """
        events = []
        try:
            while True:
                event = self.queue.get_nowait()
                events.append(event)
                self.queue.task_done()
        except asyncio.QueueEmpty:
            pass
        return events

    async def aloop_drain(self, *args, **kwargs):
        """
        loop draining the queue
        """
        events = []
        while True:
            try:
                if not events:
                    events = await self.dequeue()

                self.crud.batch_insert(events)
                # batch insertion successful reset the events to empty
                events = []
            except SQLAlchemyError:
                # sql errror while inserting do not clear the events
                pass
            except:  # pylint: disable=bare-except
                # other type of exceptions caught clear the events
                events = []
            finally:
                await asyncio.sleep(10)

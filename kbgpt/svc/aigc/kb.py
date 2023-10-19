from typing import Any, Dict, List, Optional

from sanic import Blueprint, Request, Sanic

from kbgpt.lib.tasks.manager import FuncWrapper, TaskRecord


class UpdateKBFromDB(FuncWrapper):
    def __init__(self, name: str, handle: str):
        self.name = name
        self.handle = handle

    async def __call__(self, *args: Any, app: Sanic, record: TaskRecord, **kwds: Any):
        pass

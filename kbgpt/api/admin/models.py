from datetime import datetime
from typing import Optional

from pydantic import BaseModel, root_validator

from kbgpt.api.libs.base_model import ResponseBase
from kbgpt.lib.tasks.manager import TaskRecord, TaskStatus


class TaskStatusRequest(BaseModel):
    task_id: Optional[str]
    task_name: Optional[str]

    @root_validator(pre=True)
    def check_at_least_one_present(cls, values):
        """validator"""
        assert (
            "task_id" in values or "task_name" in values
        ), "at least task_id or task_name should be present"
        return values


class TaskStatusResponse(ResponseBase):
    task_id: str
    task_name: str
    task_handle: str
    max_attempt: int
    status: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    @classmethod
    def from_orm(cls, orm: TaskRecord):
        rst = TaskStatusResponse(**orm.__dict__)
        rst.status = TaskStatus(orm.status).name
        return rst

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, root_validator, validator

from kbgpt.api.libs.base_model import ResponseBase
from kbgpt.lib.tasks.manager import TaskMutExclusive, TaskRecord, TaskStatus


class TaskStatusRequest(BaseModel):
    task_id: Optional[str]
    task_name: Optional[str]

    @root_validator(pre=True)
    def check_at_least_one_present(cls, values):  # pylint: disable=no-self-argument
        """validator"""
        assert (
            "task_id" in values or "task_name" in values
        ), "at least task_id or task_name should be present"
        return values


class SetTaskStatusRequest(TaskStatusRequest):
    status: TaskStatus


class TaskStatusResponse(ResponseBase):
    """task status response"""

    task_id: Optional[str]
    task_name: Optional[str]
    task_handle: Optional[str]
    parameters: Optional[str]
    max_attempt: Optional[int]
    attempt: Optional[int]
    status: Optional[TaskStatus]
    error: Optional[str]
    exclusive: Optional[TaskMutExclusive]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]

    @validator("exclusive", pre=True)
    def validate_exclusive(cls, value):  # pylint: disable=no-self-argument
        """validator"""
        if isinstance(value, int):
            return TaskMutExclusive(value)
        else:
            return value

    @validator("status", pre=True)
    def validate_status(cls, value):  # pylint: disable=no-self-argument
        """validator"""
        if isinstance(value, int):
            return TaskStatus(value)
        else:
            return value

    class Config:
        json_encoders = {
            TaskStatus: lambda g: g.name,
            TaskMutExclusive: lambda g: g.name,
        }

    @classmethod
    def from_orm(cls, orm: TaskRecord):
        rst = TaskStatusResponse(**orm.__dict__)
        return rst

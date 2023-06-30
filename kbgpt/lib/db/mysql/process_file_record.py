"""
doc string
"""
from typing import Any, Dict

from sqlalchemy import Column, Float, Integer

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import OBase


class ProcessFileRecord(Base, OBase):
    """
    ProcessFileRecord class
    """

    __tablename__ = "log_process_file_record"

    file_counts = Column(Integer)
    total_file_tokens = Column(Integer)
    total_file_bytes = Column(Integer)
    split_size = Column(Integer)
    total_file_splits = Column(Integer)

    @classmethod
    def create(
        cls, kwargs: Dict = None, result: Any = None, seconds_spent: Float = 0.0
    ):
        obj: ProcessFileRecord = super().create(
            kwargs=kwargs, result=result, seconds_spent=seconds_spent
        )
        obj.file_counts = result["file_counts"]
        obj.total_file_tokens = result["total_file_tokens"]
        obj.total_file_bytes = result["total_file_bytes"]
        obj.split_size = result["split_size"]
        obj.total_file_splits = result["total_file_splits"]
        return obj

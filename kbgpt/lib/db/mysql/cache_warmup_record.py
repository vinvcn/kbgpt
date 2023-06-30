"""
doc string
"""
from typing import Any, Dict

from sqlalchemy import Column, Float, Integer

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import OBase


class CacheWarmupRecord(Base, OBase):
    """
    CacheWarmupRecord class
    """

    __tablename__ = "log_cache_warmup_record"

    tokens = Column(Integer)
    cost = Column(Float)
    question_counts = Column(Integer)
    limit_hits = Column(Integer)

    @classmethod
    def create(
        cls, kwargs: Dict = None, result: Any = None, seconds_spent: Float = 0.0
    ) -> 'CacheWarmupRecord':
        obj: CacheWarmupRecord = super().create(
            kwargs=kwargs, result=result, seconds_spent=seconds_spent
        )
        obj.tokens = result["tokens"]
        obj.cost = result["cost"]
        obj.question_counts = result["question_counts"]
        obj.limit_hits = result["limit_hits"]
        return obj

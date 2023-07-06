"""
doc string
"""
from typing import Dict

from sqlalchemy import Boolean, Column, Float, Integer, Text

from kbgpt.api.aigc.qa_models import QAResponse
from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import OBase


class QARecord(Base, OBase):
    """
    QARecord class
    """

    __tablename__ = "log_qa_record"

    question = Column(Text(collation="utf8mb4_unicode_ci"))
    answer = Column(Text(collation="utf8mb4_unicode_ci"))
    tokens = Column(Integer)
    cost = Column(Float)
    hit_cache = Column(Boolean)
    streaming = Column(Boolean)

    @classmethod
    def create(
        cls, kwargs: Dict = None, result: QAResponse = None, seconds_spent: Float = 0.0
    ) -> "QARecord":
        obj: QARecord = super().create(
            kwargs=kwargs, result=result, seconds_spent=seconds_spent
        )
        obj.question = kwargs["question"]
        obj.streaming = kwargs["streaming"]
        obj.answer = result.answer
        obj.tokens = result.total_tokens
        obj.hit_cache = result.hit_cache
        return obj

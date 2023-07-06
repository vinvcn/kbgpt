from typing import Dict

from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from kbgpt.api.senti.models import Sentiment, SentimentResponse
from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import OBase


class SentimentRecord(Base, OBase):
    """
    QARecord class
    """

    __tablename__ = "log_sentiment_record"

    success = Column(Boolean)
    rating = Column(Integer)
    prompt_tokens = Column(Integer)
    comp_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Float)
    level = Column(Integer)
    description = Column(String(100, collation="utf8mb4_unicode_ci"))
    content = Column(Text(collation="utf8mb4_unicode_ci"))

    @classmethod
    def create(
        cls,
        kwargs: Dict = None,
        result: SentimentResponse = None,
        seconds_spent: Float = 0.0,
    ) -> "SentimentRecord":
        obj: SentimentRecord = super().create(
            kwargs=kwargs, result=result, seconds_spent=seconds_spent
        )
        request: Sentiment = kwargs["req"]

        obj.update(**request.__dict__)
        obj.update(**result.__dict__)
        return obj

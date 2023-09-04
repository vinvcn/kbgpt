from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import UtilityMixin


class HumanRating(Base, UtilityMixin):
    """
    Jinja Template Record
    """

    __tablename__ = "rating_human_rating"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, nullable=False)
    invoke_id = Column(String(128, collation="utf8mb4_unicode_ci"))
    node_id = Column(String(128, collation="utf8mb4_unicode_ci"))
    rater = Column(String(64, collation="utf8mb4_unicode_ci"))
    rating = Column(String(128, collation="utf8mb4_unicode_ci"), default="")
    comment = Column(String(128, collation="utf8mb4_unicode_ci"))
    timestamp = Column(DateTime, default=datetime.utcnow)


class Rater(Base, UtilityMixin):
    """
    Jinja Template Record
    """

    __tablename__ = "rating_human_rater"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64, collation="utf8mb4_unicode_ci"))
    timestamp = Column(DateTime, default=datetime.utcnow)

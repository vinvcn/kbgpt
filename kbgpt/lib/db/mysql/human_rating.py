from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from kbgpt.lib.db.mysql import Base


class HumanRating(Base):
    """
    Jinja Template Record
    """

    __tablename__ = "rating_human_rating"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer)
    invoke_id = Column(String(128, collation="utf8mb4_unicode_ci"))
    rater = Column(String(64, collation="utf8mb4_unicode_ci"))
    rating = Column(Integer)
    comment = Column(String(128, collation="utf8mb4_unicode_ci"))

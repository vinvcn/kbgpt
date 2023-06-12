"""
doc string
"""
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
)
from kbgpt.lib.db.mysql import Base


class VirtualCommentRecord(Base):
    """
    VirtualCommentRecord class
    """

    __tablename__ = "log_virtual_comment_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoke_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    type = Column(String(25, collation="utf8mb4_unicode_ci"))
    post_id = Column(Integer)
    content = Column(Text(collation="utf8mb4_unicode_ci"))
    timestamp = Column(DateTime)
    success = Column(Boolean)
    result = Column(Text(collation="utf8mb4_unicode_ci"))
    tokens = Column(Integer)
    cost = Column(Float)

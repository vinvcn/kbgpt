from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import OBase


class JinjaTemplateRecord(OBase, Base):
    """
    Jinja Template Record
    """

    __tablename__ = "log_jinja_engine_record"

    node_id = Column(String(128, collation="utf8mb4_unicode_ci"))
    step_name = Column(String(64, collation="utf8mb4_unicode_ci"))
    prompt = Column(Text(collation="utf8mb4_unicode_ci"))
    result = Column(Text(collation="utf8mb4_unicode_ci"))
    usage = Column(Text(collation="utf8mb4_unicode_ci"))

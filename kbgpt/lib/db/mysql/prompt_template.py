from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from kbgpt.lib.db.mysql import Base


class PromptTemplate(Base):
    """prompt template table"""

    __tablename__ = "prompt_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(50, collation="utf8mb4_unicode_ci"))
    body = Column(Text(collation="utf8mb4_unicode_ci"))
    keywords = Column(String(50, collation="utf8mb4_unicode_ci"))
    timestamp = Column(DateTime, default=datetime.utcnow)

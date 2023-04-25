from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base

from config import profile

# Create an engine that connects to your database (in this case, SQLite)
engine = create_engine(profile.qa.db_url, echo=True)

# Create a base class for your models to inherit from
Base = declarative_base()


# Define a model class with some columns
class QARecord(Base):
    """
    QA record class
    """

    __tablename__ = "kbgpt_qa_record"

    id = Column(Integer, primary_key=True)
    # f1c96a14-7292-3ab5-b420-1982a39b1b11
    device_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    # xxx.xxx.xxx.xxx
    ip = Column(String(20, collation="utf8mb4_unicode_ci"))
    question = Column(Text(2000, collation="utf8mb4_unicode_ci"))
    question_embedding = Column(String(255, collation="utf8mb4_unicode_ci"))
    answer = Column(Text(2000, collation="utf8mb4_unicode_ci"))
    answer_type = Column(String(50, collation="utf8mb4_unicode_ci"))
    total_tokens = Column(Integer)
    total_cost = Column(Float)
    total_seconds = Column(Float)
    timestamp = Column(DateTime)


# Create the table(s) in the database by calling create_all on the Base class
Base.metadata.create_all(engine)

from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base


# Create an engine that connects to your database (in this case, SQLite)
engine = create_engine("DB_URL", echo=True)

# Create a base class for your models to inherit from
Base = declarative_base()


# Define a model class with some columns
class FileRecord(Base):
    """
    FileRecord class
    """

    __tablename__ = "file_record"

    id = Column(Integer, primary_key=True)
    name = Column(String(255, collation="utf8mb4_unicode_ci"))
    hashing = Column(String(255, collation="utf8mb4_unicode_ci"))
    content_type = Column(String(20, collation="utf8mb4_unicode_ci"))
    path = Column(String(500, collation="utf8mb4_unicode_ci"))
    redis_index = Column(String(500, collation="utf8mb4_unicode_ci"))
    embedding = Column(Boolean)


# Create the table(s) in the database by calling create_all on the Base class
Base.metadata.create_all(engine)

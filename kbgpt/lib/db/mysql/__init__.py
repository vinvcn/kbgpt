"""
doc string
"""

__all__ = ["Crud", "Base"]

from config import profile
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from traceback import print_exc
from sqlalchemy.orm import sessionmaker

# Create a base class for your models to inherit from
Base = declarative_base()


class Crud:
    def __init__(
        self,
        connection_string=profile.db_url,
        encoding="utf-8",
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    ):
        self.connection_string = connection_string
        self.encoding = encoding
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.engine = None
        self.session = None

    def _create_engine(self):
        self.engine = sqlalchemy.create_engine(self.connection_string, echo=True)

    def create_session(self):
        self._create_engine()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        self._create_engine()
        Base.metadata.create_all(self.engine)

    def insert(self, instances):
        try:
            self.session.add(instances)
            self.session.commit()
            self.session.flush()
        except:
            self.session.rollback()
            raise

    def batch_insert(self, list_of_inst):
        self.session.bulk_save_objects(list_of_inst)
        self.session.commit()

    def __del__(self):
        self.close_all_connections()

    def close_session(self):
        try:
            self.session.close()
        except:
            print_exc()
        else:
            self.session = None

    def close_all_connections(self):
        try:
            self.engine.dispose()
        except:
            print_exc()
        else:
            self.engine = None

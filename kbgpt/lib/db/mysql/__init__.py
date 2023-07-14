"""
doc string
"""

__all__ = ["Crud", "Base"]

import logging
from traceback import print_exc
from typing import Dict, Type

import sqlalchemy
from sanic import Sanic
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from config import profile
from kbgpt.api.libs.resources import LifeCycleMixin

# Create a base class for your models to inherit from
Base = declarative_base()


class Crud(LifeCycleMixin):
    """
    CRUD operations for MySQL
    """

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

    async def init(self, app: Sanic=None):
        self._create_engine()
        self._create_session()
        self._create_tables()

    async def destroy(self, app: Sanic=None):
        self.close_session()
        self.close_all_connections()

    def _create_engine(self):
        self.engine = sqlalchemy.create_engine(self.connection_string, echo=True)

    def _create_session(self):
        session = sessionmaker(bind=self.engine)
        self.session = session()

    def _create_tables(self):
        Base.metadata.create_all(self.engine)

    def batch_insert(self, list_of_inst):
        """insert the records in batch"""
        try:
            self.session.bulk_save_objects(list_of_inst)
            self.session.commit()
        except SQLAlchemyError as e:
            logging.exception(e)
            self.session.rollback()
            raise e

    def get_first_by(self, cls: Type[Base], filter_params: Dict, order_col: str):
        return (
            self.session.query(cls)
            .filter_by(**filter_params)
            .order_by(text(f"{order_col} desc"))
            .first()
        )

    def __del__(self):
        self.close_all_connections()

    def close_session(self):
        """close the sessioin"""
        if not self.session:
            return
        try:
            self.session.close()
        except SQLAlchemyError as e:
            logging.exception(e)
        else:
            self.session = None

    def close_all_connections(self):
        """close all connections"""
        if not self.engine:
            return
        try:
            self.engine.dispose()
        except SQLAlchemyError as e:
            logging.exception(e)
        else:
            self.engine = None

"""
doc string
"""

__all__ = ["Crud", "Base"]

import logging
from math import ceil
from traceback import print_exc
from typing import Any, Dict, List, Type

import sqlalchemy
from sanic import Sanic
from sqlalchemy import update
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

    async def init(self, app: Sanic = None):
        self._create_engine()
        self._create_tables()

    async def destroy(self, app: Sanic = None):
        self.close_all_connections()

    def _create_engine(self):
        self.engine = sqlalchemy.create_engine(self.connection_string, echo=False)

    def _create_tables(self):
        Base.metadata.create_all(self.engine)

    def truncate_table(self, table_name):
        with sessionmaker(bind=self.engine)() as session:
            session.execute(text(f"TRUNCATE TABLE {table_name}"))
            session.commit()

    def add(self, entry):
        with sessionmaker(bind=self.engine)() as session:
            session.add(entry)
            session.commit()

    def batch_insert(self, list_of_inst):
        """insert the records in batch"""
        with sessionmaker(bind=self.engine)() as session:
            session.bulk_save_objects(list_of_inst)
            session.commit()

    def update_rows(self, cls: Type[Base], rows):
        with sessionmaker(bind=self.engine)() as session:
            if isinstance(rows, list):
                entries = [r.__dict__ for r in rows]
            else:
                entries = [rows.__dict__]

            session.bulk_update_mappings(cls, entries)
            session.commit()

    def get_first_by(self, cls: Type[Base], filter_params: Dict, order_col: str):
        with sessionmaker(bind=self.engine)() as session:
            result = (
                session.query(cls)
                .filter_by(**filter_params)
                .order_by(text(f"{order_col} desc"))
                .first()
            )
            return result

    def get_all(
        self,
        cls: Type[Base],
        the_filter: sqlalchemy.ColumnElement[bool] = None,
        order_by: sqlalchemy.ColumnElement[Any] = None,
        limit: int = None,
    ):
        with sessionmaker(bind=self.engine)() as session:
            query = session.query(cls)
            if the_filter is not None:
                query = query.filter(the_filter)
            if order_by is not None:
                query = query.order_by(order_by)
            if limit is not None:
                query = query.limit(limit)
            return query.all()

    def get_max_page(
        self,
        cls: Type[Base] | List[Type[Base]],
        the_filter: sqlalchemy.ColumnElement[bool] = None,
        order_col: sqlalchemy.ColumnElement[Any] = None,
        join_on: sqlalchemy.ColumnElement[Any] = None,
        on_clause: sqlalchemy.ColumnElement[bool] = None,
        item_per_page: int = 5,
    ):
        with sessionmaker(bind=self.engine)() as session:
            if not isinstance(cls, list):
                cls = [cls]
            query = session.query(*cls)
            if the_filter is not None:
                query = query.filter(the_filter)
            if order_col is not None:
                query = query.order_by(order_col)
            if join_on is not None and on_clause is not None:
                query = query.outerjoin(join_on, on_clause)
            count = query.count()
            return ceil(count / item_per_page)

    def get_page_order_by(
        self,
        cls: Type[Base] | List[Type[Base]],
        the_filter: sqlalchemy.ColumnElement[bool],
        order_col: sqlalchemy.ColumnElement[Any],
        join_on: sqlalchemy.ColumnElement[Any] = None,
        on_clause: sqlalchemy.ColumnElement[bool] = None,
        page: int = 1,
        item_per_page: int = 5,
    ):
        with sessionmaker(bind=self.engine)() as session:
            if not isinstance(cls, list):
                cls = [cls]
            query = session.query(*cls)
            if the_filter is not None:
                query = query.filter(the_filter)
            if order_col is not None:
                query = query.order_by(order_col)
            if join_on is not None and on_clause is not None:
                query = query.outerjoin(join_on, on_clause)
            query = query.offset((page - 1) * item_per_page).limit(item_per_page)
            return query.all()

    def get_one(
        self,
        cls: Type[Base],
        the_filter: sqlalchemy.ColumnElement[bool] = None,
        order_by: sqlalchemy.ColumnElement[Any] = None,
    ):
        results = self.get_all(cls, the_filter, order_by, 1)
        if results:
            return results[0]

    def __del__(self):
        self.close_all_connections()

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

    def select_all_by_join(self):
        pass

import json
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


class UtilityMixin:
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def as_json(self):
        return json.dumps(self.as_dict(), indent=4, cls=DatetimeEncoder)


class OBase(UtilityMixin):
    """base record"""

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoke_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    seconds_spent = Column(Float)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create(
        cls, kwargs: Dict = None, result: Any = None, seconds_spent: Float = 0.0
    ):
        """create method"""
        obj = cls()
        obj.timestamp = datetime.utcnow()
        obj.invoke_id = uuid4().hex
        obj.seconds_spent = seconds_spent
        return obj

import abc
from abc import abstractmethod
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, root_validator


class SelectionFailed(Exception):
    pass


class Key(metaclass=abc.ABCMeta):
    @abstractmethod
    def get_from(self, obj: Any):
        pass


class Sub(Key):
    def __init__(self, index):
        self.index = index

    def __str__(self):
        return str(self.index)

    def get_from(self, obj: Any):
        if isinstance(obj, list) or isinstance(obj, tuple):
            return obj[self.index]
        raise SelectionFailed(f"type mismatch object {obj} is neither list or tuple")


class Ky(Key):
    def __init__(self, name: str, sub: Optional[Sub] = None):
        self.name = name
        self.sub = sub

    def __str__(self):
        substr = f"[{self.sub}]" if self.sub else ""
        return f"{self.name}{substr}"

    def get_from(self, obj: Any):
        if isinstance(obj, dict):
            sub_obj = obj[self.name]
            return self.sub.get_from(sub_obj) if self.sub else sub_obj
        elif isinstance(obj, BaseModel):
            sub_obj = obj.dict()[self.name]
            return self.sub.get_from(sub_obj) if self.sub else sub_obj
        else:
            raise SelectionFailed(
                f"type mismatch object {obj} is neither dict nor BaseModel"
            )


class Selector(BaseModel):
    node: str = Field("")
    key: str
    to_key: str = Field("")

    class Config:
        frozen = True

    @root_validator(pre=True)
    def validate_key_and_tokey(cls, values: dict):
        key, to_key = values.get("key"), values.get("to_key")
        if not to_key and "." in key:
            raise ValueError(
                f"Ambiguity while validating, key '{key}' contains dot "
                + "while to_key is not given, it can not be used as the "
                + "default to_key "
            )
        return values

    def with_to_key(self, to_key: str):
        return self.copy(update={"to_key": to_key})


class MultiplexerType(Enum):
    ALL = "all"
    ANY = "any"
    # FIRST = "first"
    NONE = "none"


class SelectorMultiplexer(BaseModel):
    selectors: List[Selector]
    mode: MultiplexerType = Field(MultiplexerType.ALL)

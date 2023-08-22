from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class Selector(BaseModel):
    node: str = Field("")
    key: str = Field("")
    to_key: str = Field("")

    class Config:
        frozen = True

    def with_to_key(self, to_key: str):
        return self.copy(update={"to_key": to_key})


class MultiplexerType(Enum):
    ALL = "all"
    SOME = "some"
    FIRST = "first"


class SelectorMultiplexer(BaseModel):
    selectors: List[Selector]
    mode: MultiplexerType = Field(MultiplexerType.ALL)

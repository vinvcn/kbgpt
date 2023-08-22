from collections import namedtuple
from typing import Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from kbgpt.lib.exec.engines.configs.models import EngineTypes
from kbgpt.lib.exec.pipeline.checker_models import CheckerTypes
from kbgpt.lib.exec.pipeline.selector_models import Selector, SelectorMultiplexer


class Node(BaseModel):
    engine: Optional[EngineTypes] = Field(None, discriminator="type")
    id: str
    frm: Optional[SelectorMultiplexer]
    sel: Dict[str, str] = Field({})
    pre: Optional[CheckerTypes]
    post: Optional[CheckerTypes]

    # pylint: disable = E0213:no-self-argument
    @validator("id", pre=True)
    def validate_id(val):
        """validate id field"""
        if not val:
            return str(uuid4())
        else:
            return val

    def __repr__(self) -> str:
        return f"Node[id:{self.id},engine:{repr(self.engine)}]"

    @property
    def selectors(self):
        if self.engine.out_keys:
            Selectors = namedtuple("Selectors", self.engine.out_keys)
            return Selectors(
                *[Selector(node=self.id, key=k) for k in self.engine.out_keys]
            )

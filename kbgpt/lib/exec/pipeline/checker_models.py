from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class CheckerMod(BaseModel):
    type: Literal["type"]
    key: str


class InListCheckerMod(CheckerMod):
    type: Literal["in_list"] = Field("in_list")
    trg_list: Optional[List[Any]]


class EqCheckerMod(CheckerMod):
    type: Literal["eq"] = Field("eq")
    trg_value: Optional[Any]


class EvalCheckerMod(CheckerMod):
    type: Literal["eval"] = Field("eval")
    eval_exp: str


_CheckerTypes = Union[InListCheckerMod, EqCheckerMod, EvalCheckerMod]
CheckerTypes = Union[_CheckerTypes, List[_CheckerTypes]]

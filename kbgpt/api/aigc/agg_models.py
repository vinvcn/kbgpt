from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from kbgpt.api.libs.base_model import ResponseBase
from kbgpt.lib.llm.openai import Message


class AGGRequest(BaseModel):
    history: Optional[Tuple[Message, ...]]
    question: str
    threshold: int = Field(80)


class AGGResponse(ResponseBase):
    message: Optional[str]
    recommend: Optional[List[str]]
    product: Optional[str]


class Matching(BaseModel):
    id: int
    name: Optional[str]
    score: Optional[int] = Field(None, le=100, ge=0)
    intent: Optional[str]


class IntentResp(BaseModel):
    matching: Optional[List[Matching]] = Field([])
    match_names: Optional[List[str]] = Field([])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

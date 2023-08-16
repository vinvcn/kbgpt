"""
qa api models
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from kbgpt.api.aigc.agg_models import Matching
from kbgpt.api.libs.base_model import OpenAIResponseBase


class Question(BaseModel):
    """question"""

    question: str
    threshold: float = Field(0.17)


class QAResponse(OpenAIResponseBase):
    """qa response"""

    answer: str
    intents: Optional[List[Matching]]
    total_tokens: Optional[int]
    total_cost: Optional[float]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    successful_requests: Optional[int]
    hit_cache: Optional[bool]

    def json(self, *args, **kwargs) -> str:
        json_str = super().json(*args, ensure_ascii=False, **kwargs)
        return json_str.replace("\\n", "<br/>")


class GetRecomm(BaseModel):
    """get recommendation"""

    product_id: Optional[int]
    product_name: Optional[str]


class DocInfo(OpenAIResponseBase):
    """document information"""

    version: str
    timestamp: datetime

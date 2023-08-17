"""
qa api models
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from kbgpt.api.aigc.agg_models import Matching
from kbgpt.api.libs.base_model import OpenAIResponseBase


class RecommType(Enum):
    SIMILARITY = "similarity"
    GPT4 = "gpt4"
    GPT3_5 = "gpt3.5"


class Question(BaseModel):
    """question"""

    question: str
    athreshold: float = Field(0.17)
    cthreshold: float = Field(0.17)
    temperature: float = Field(0.7)
    recomm_type: RecommType = Field(RecommType.GPT4)


class QAResponse(OpenAIResponseBase):
    """qa response"""

    answer: Optional[str]
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

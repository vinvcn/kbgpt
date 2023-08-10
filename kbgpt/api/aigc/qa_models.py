"""
qa api models
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from kbgpt.api.aigc.agg import Matching
from kbgpt.api.libs.base_model import OpenAIResponseBase


class Question(BaseModel):
    """question"""

    question: str


class QAResponse(OpenAIResponseBase):
    """qa response"""

    answer: str
    # intents: Optional[List[Matching]]
    total_tokens: int
    total_cost: float
    prompt_tokens: int
    completion_tokens: int
    successful_requests: int
    hit_cache: bool

    def json(self, *args, **kwargs) -> str:
        json_str = super().json(*args, ensure_ascii=False, **kwargs)
        return json_str.replace("\\n", "<br/>")


class DocInfo(OpenAIResponseBase):
    """document information"""

    version: str
    timestamp: datetime

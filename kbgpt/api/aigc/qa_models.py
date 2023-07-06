"""
qa api models
"""
from datetime import datetime

from pydantic import BaseModel

from kbgpt.api.libs.base_model import ResponseBase


class Question(BaseModel):
    """question"""

    question: str


class QAResponse(ResponseBase):
    """qa response"""

    answer: str
    total_tokens: int
    total_cost: float
    prompt_tokens: int
    completion_tokens: int
    successful_requests: int
    hit_cache: bool


class DocInfo(ResponseBase):
    """ document information """

    version: str
    timestamp: datetime

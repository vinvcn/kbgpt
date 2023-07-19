from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel

from kbgpt.api.libs.base_model import OpenAIResponseBase, ResponseBase


class Type(Enum):
    WEEKLY = "weekly"
    DAILY = "daily"


class Report(BaseModel):
    type: Type
    date: date
    polish: Optional[bool]
    data: Optional[Dict[str, Any]]


class ReportResponse(OpenAIResponseBase):
    content: str
    polish_content: str
    data: str
    caption: Optional[str]


class ToVoice(BaseModel):
    content: str


class ToVoiceResponse(ResponseBase):
    uri: str
    expires: int

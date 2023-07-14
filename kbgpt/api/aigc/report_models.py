from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from kbgpt.api.libs.base_model import OpenAIResponseBase, ResponseBase


class Type(Enum):
    WEEKLY = "weekly"
    DAILY = "daily"


class Report(BaseModel):
    type: Type
    date: Optional[date]
    polish: Optional[bool]


class ReportResponse(OpenAIResponseBase):
    content: str
    data: str
    caption: Optional[str]


class ToVoice(BaseModel):
    content: str


class ToVoiceResponse(ResponseBase):
    uri: str
    expires: int

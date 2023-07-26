from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from kbgpt.api.libs.base_model import OpenAIResponseBase, ResponseBase


class Type(Enum):
    WEEKLY = "weekly"
    DAILY = "daily"


class Report(BaseModel):
    type: Type
    date: date
    polish: Optional[bool]
    data: Optional[Dict[str, Any]]
    sync: bool = Field(False)


class ReportResponse(OpenAIResponseBase):
    content: str
    polish_content: str
    data: str
    caption: Optional[str]


class MediaReportResp(OpenAIResponseBase):
    content: str
    ssml: str
    pages: List[str]
    data: str


class ToVoice(BaseModel):
    ssml: str
    pages: List[str]


class ToVoiceResponse(ResponseBase):
    uri: str
    timepoints: str
    expires: int

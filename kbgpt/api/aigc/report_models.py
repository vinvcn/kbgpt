from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from kbgpt.api.libs.base_model import OpenAIResponseBase, ResponseBase


class Type(Enum):
    WEEKLY = "weekly"
    DAILY = "daily"
    MONTHLY = "monthly"


class Report(BaseModel):
    type: Type
    date: date
    polish: Optional[bool]
    data: Optional[Dict[str, Any]]
    sync: bool = Field(False)

    @validator("date", pre=True)
    def validate_date(cls, v):
        if isinstance(v, str):
            if len(v.split("-")) == 2:
                return datetime.strptime(v, "%Y-%m").date()
            else:
                return datetime.strptime(v, "%Y-%m-%d").date()
        elif isinstance(v, date):
            return v
        else:
            raise ValueError(f"invalid value {v} for date")


class ReportResponse(OpenAIResponseBase):
    content: str
    polish_content: str
    data: str
    caption: Optional[str]


class MediaReportResp(OpenAIResponseBase):
    content: str
    ssml: str
    pages: List[str]
    polish_content: str
    data: str


class ToVoice(BaseModel):
    ssml: str
    pages: List[str]


class ToVoiceResponse(ResponseBase):
    uri: str
    timepoints: str
    expires: int

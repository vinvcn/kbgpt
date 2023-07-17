from enum import Enum
from typing import List, Optional

import aiohttp
from pydantic import BaseModel

from config import profile


class SourceType(Enum):
    TEMPLATE = 1
    AIGC = 2

class ReportType(Enum):
    DAILY = 1
    WEEKLY = 2


class CreateReport(BaseModel):
    caption: Optional[str]
    content: Optional[str]
    data: Optional[str]
    image: Optional[str]
    source: Optional[int]
    type: Optional[int]
    video: Optional[str]
    video_cover: Optional[str]
    voice: Optional[str]


class CreateReportReq(BaseModel):
    items: List[CreateReport]


class BackendAdmin:
    async def create_report(self, rpts: List[CreateReport]):
        """http get request"""
        req = CreateReportReq(items=rpts)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=profile.report.backend_admin_url, json=req.dict(exclude_none=True)
            ) as response:
                data = await response.text()
                return data

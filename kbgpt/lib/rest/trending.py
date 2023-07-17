from datetime import date
from enum import Enum
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel

from config import profile
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.lib.rest.be_admin import ReportType


class TrendParam(BaseModel):
    """trend param"""

    dateParam: date
    reportType: ReportType

    class Config:
        """config"""

        json_encoders = {
            date: lambda v: v.strftime("%Y-%m-%d"),
        }


class TrendRequest(BaseModel):
    params: TrendParam


class TrendingClient:
    async def fetch_data(self, req: TrendRequest):
        target_url = urljoin(
            profile.report.trending_url, "mb-market-data-service/tob/fund/getAIGCReport"
        )
        headers = {"content-type": API_CONTENT_TYPE}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url=target_url, data=req.json(exclude_none=True)
            ) as response:
                data = await response.json()
                return data

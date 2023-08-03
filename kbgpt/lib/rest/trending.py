import logging
from datetime import date
from enum import Enum
from typing import Literal, Optional, Union
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel, Field

from config import profile
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.lib.rest.be_admin import ReportType


class TrendParam(BaseModel):
    """trend param"""

    dateParam: Optional[str]
    reportType: Literal[ReportType.DAILY, ReportType.WEEKLY]


class MonthTrendParam(BaseModel):
    dateParam: Optional[str]
    reportType: Literal[ReportType.MONTHLY]


class TrendRequest(BaseModel):
    params: Union[TrendParam, MonthTrendParam] = Field(..., discriminator="reportType")

    class Config:
        """config"""

        json_encoders = {MonthTrendParam: MonthTrendParam.__json_encoder__}


class TrendingClient:
    async def fetch_data(self, req: TrendRequest):
        target_url = urljoin(
            profile.report.trending_url, "mb-market-data-service/tob/fund/getAIGCReport"
        )
        logging.info(target_url)
        headers = {"content-type": API_CONTENT_TYPE}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url=target_url, data=req.json(exclude_none=True)
            ) as response:
                data = await response.json()
                return data

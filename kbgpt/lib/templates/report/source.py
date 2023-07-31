import logging
from datetime import date
from typing import Any

from kbgpt.api.aigc.report_models import Report, Type
from kbgpt.lib.rest.be_admin import ReportType
from kbgpt.lib.rest.trending import (
    MonthTrendParam,
    TrendingClient,
    TrendParam,
    TrendRequest,
)
from kbgpt.lib.templates.report.models.daily_data import DailyData
from kbgpt.lib.templates.report.models.monthly_data import MonthlyData
from kbgpt.lib.templates.report.models.weekly_data import WeeklyData


class DataFetchingError(Exception):
    """fetching data failed"""


class ReportDataSource:
    """report data source"""

    async def __call__(self, req: Report) -> Any:
        r_type: ReportType = (
            ReportType.DAILY
            if req.type == Type.DAILY
            else ReportType.WEEKLY
            if req.type == Type.WEEKLY
            else ReportType.MONTHLY
        )

        if req.data:
            return (
                DailyData.parse_obj(req.data)
                if r_type == ReportType.DAILY
                else WeeklyData.parse_obj(req.data)
                if r_type == ReportType.WEEKLY
                else MonthlyData.parse_obj(req.data)
            )

        params = (
            MonthTrendParam(dateParam=dt.strftime("%Y-%m"), reportType=r_type)
            if r_type == ReportType.MONTHLY
            else TrendParam(dateParam=dt.strftime("%Y-%m-%d"), reportType=r_type)
        )

        result_obj = await TrendingClient().fetch_data(TrendRequest(params=params))
        logging.info(result_obj)
        if result_obj["errCode"] != 0:
            raise DataFetchingError(result_obj["message"])

        if "data" not in result_obj:
            raise DataFetchingError("No data Present")

        return (
            DailyData.parse_obj(result_obj["data"])
            if r_type == ReportType.DAILY
            else WeeklyData.parse_obj(result_obj["data"])
            if r_type == ReportType.WEEKLY
            else MonthlyData.parse_obj(result_obj["data"])
        )

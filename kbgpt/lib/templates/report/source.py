import logging
from datetime import date
from typing import Any

from kbgpt.api.aigc.report_models import Report
from kbgpt.lib.rest.be_admin import ReportType
from kbgpt.lib.rest.trending import TrendingClient, TrendParam, TrendRequest
from kbgpt.lib.templates.report.models.daily_data import DailyData
from kbgpt.lib.templates.report.models.weekly_data import WeeklyData


class DataFetchingError(Exception):
    """fetching data failed"""


class ReportDataSource:
    """report data source"""

    async def __call__(self, req: Report) -> Any:
        r_type: ReportType = (
            ReportType.DAILY if req.type.value == "daily" else ReportType.WEEKLY
        )

        if req.data:
            if r_type == ReportType.DAILY:
                return DailyData.parse_obj(req.data)
            else:
                return WeeklyData.parse_obj(req.data)

        result_obj = await TrendingClient().fetch_data(
            TrendRequest(params=TrendParam(dateParam=req.date, reportType=r_type))
        )
        logging.info(result_obj)
        if result_obj["errCode"] != 0:
            raise DataFetchingError(result_obj["message"])

        if "data" not in result_obj:
            raise DataFetchingError("No data Present")

        if r_type is ReportType.DAILY:
            return DailyData.parse_obj(result_obj["data"])
        else:
            return WeeklyData.parse_obj(result_obj["data"])

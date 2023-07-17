import abc
import asyncio
import datetime
from datetime import date, timedelta
from os.path import abspath, dirname, join

from pydantic import BaseModel

from config import profile
from kbgpt.lib.templates.constants import REPO_DIR
from kbgpt.lib.templates.report.models import config
from kbgpt.lib.templates.report.models.daily_data import DailyData
from kbgpt.lib.templates.report.models.weekly_data import WeeklyData


class StatsProvider(metaclass=abc.ABCMeta):
    """
    Abstract base class for all stats providers.
    """

    @abc.abstractmethod
    async def __call__(
        self, dt: datetime.date
    ) -> BaseModel:
        """
        Get data for a specific date range.

        Args:
            start_date (datetime.date): The start date of the stats.
            end_date (datetime.date): The end date of the stats.

        Returns:
            pydantic.BaseModel: Fetched data as a Pydantic BaseModel.
        """


class WeeklyReport(StatsProvider):
    async def __call__(self, dt: date) -> WeeklyData:
        return WeeklyData.parse_raw(
            """
{
    "startTradeDate": "2023-07-03",
    "endTradeDate": "2023-07-07",
    "nifty50": {
        "preClose": 19497.3,
        "openPrice": 19422.8,
        "closePrice": 19600.8
    },
    "sensex50": {
        "preClose": 20325.86,
        "openPrice": 20361.86,
        "closePrice": 20000.86
    },
    "weekLyOpenAum": 3.8473882378E10,
    "weekLyCloseAum": 3.8473862178E10,
    "risingSectors": {
        "sectorName": "Debt",
        "openAum": 1.2882378E7,
        "closeAum": 1.2982378E7
    },
    "downingSectors": {
        "sectorName": "Semiconductor",
        "openAum": 2.222882378E9,
        "closeAum": 2.322182378E9
    },
    "equityFundMarket": {
        "avgReturn": 0.02,
        "numberOfRising": 23,
        "numberOfDowning": 33,
        "numberOfRisingOverFivePercent": 11,
        "topRisingIsin": "INF179KC1EM2",
        "topRisingFundName": "HDFC Gilt Fund",
        "topRisingChange": 0.18
    },
    "debtFundMarket": {
        "avgReturn": 0.012,
        "numberOfRising": 11,
        "numberOfDowning": 25
    },
    "topRisingFunds": [
        {
            "isin": "INF179KC1EM2",
            "name": "HDFC Nifty G-Sec Sep 2032 Index Fund",
            "navChange": 0.123
        },
        {
            "isin": "INF179KC1FT4",
            "name": "HDFC NIFTY G-Sec Jun 2036 Index Fund",
            "navChange": 0.0971
        },
        {
            "isin": "INF179K01756",
            "name": "HDFC Gilt Fund",
            "navChange": 0.0929
        },
        {
            "isin": "INF179KC1EK6",
            "name": "HDFC Nifty G-Sec Jun 2027 Index Fund",
            "navChange": 0.0913
        },
        {
            "isin": "INF179K01962",
            "name": "HDFC Income Fund",
            "navChange": 0.0894
        }
    ],
    "topDowningFunds": [
        {
            "isin": "INF179KC1EM2",
            "name": "HDFC Nifty G-Sec Sep 2032 Index Fund",
            "navChange": 0.123
        },
        {
            "isin": "INF179KC1FT4",
            "name": "HDFC NIFTY G-Sec Jun 2036 Index Fund",
            "navChange": 0.0971
        },
        {
            "isin": "INF179K01756",
            "name": "HDFC Gilt Fund",
            "navChange": 0.0929
        },
        {
            "isin": "INF179KC1EK6",
            "name": "HDFC Nifty G-Sec Jun 2027 Index Fund",
            "navChange": 0.0913
        },
        {
            "isin": "INF179K01962",
            "name": "HDFC Income Fund",
            "navChange": 0.0894
        }
    ]
}
"""
        )


class DailyReport(StatsProvider):
    async def __call__(self, dt, **kwargs) -> DailyData:
        """
        Fetch top funds-related stats.

        Args:
            start_date (datetime.date): The start date of the stats.
            end_date (datetime.date): The end date of the stats.

        Returns:
            pydantic.BaseModel: Fetched top funds data as a Pydantic BaseModel.
        """

        return DailyData.parse_raw(
            """
{
        "date": "2023-07-11",
        "nifty50": {
            "preClose": 19497.3,
            "openPrice": 19422.8,
            "closePrice": 19331.8
        },
        "sensex50": {
            "preClose": 20325.86,
            "openPrice": 20361.86,
            "closePrice": 20325.86
        },
        "equityFundMarket": {
            "numberOfRising": 23,
            "numberOfDowning": 33,
            "numberOfRisingOverOnePercent": 11,
            "numberOfDowningOverOnePercent": 19
        },
        "debtFundMarket": {
            "numberOfRising": 11,
            "numberOfDowning": 25
        },
        "topRisingFunds": [
            {
                "isin": "INF179KC1EM2",
                "name": "HDFC Nifty G-Sec Sep 2032 Index Fund",
                "navChange": 0.123
            },
            {
                "isin": "INF179KC1FT4",
                "name": "HDFC NIFTY G-Sec Jun 2036 Index Fund",
                "navChange": 0.0971
            },
            {
                "isin": "INF179K01756",
                "name": "HDFC Gilt Fund",
                "navChange": 0.0929
            },
            {
                "isin": "INF179KC1EK6",
                "name": "HDFC Nifty G-Sec Jun 2027 Index Fund",
                "navChange": 0.0913
            },
            {
                "isin": "INF179K01962",
                "name": "HDFC Income Fund",
                "navChange": 0.0894
            }
        ]
    }
"""
        )


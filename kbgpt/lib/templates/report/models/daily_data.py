from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from kbgpt.lib.templates.constants import REPORT_BIGGEST_RATIO

from .utils import round  # pylint: disable=redefined-builtin


class TopRisingFund(BaseModel):
    isin: str
    name: str
    navChange: float

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.navChange = round(self.navChange, 2)


class EquityFundMarket(BaseModel):
    totalFundNumber: int
    numberOfRising: int
    risingPercentage: float = Field(0.0)
    numberOfDowning: int
    downingPercentage: float = Field(0.0)
    risingAndDowningRatio: float = Field(0.0)
    numberOfRisingOverOnePercent: int
    numberOfDowningOverOnePercent: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.risingPercentage = round(
            100 * (self.numberOfRising / self.totalFundNumber), 2
        )
        self.downingPercentage = round(
            100 * (self.numberOfDowning / self.totalFundNumber), 2
        )
        if self.numberOfDowning <= 0:
            self.risingAndDowningRatio = REPORT_BIGGEST_RATIO
        else:
            self.risingAndDowningRatio = round(
                self.numberOfRising / self.numberOfDowning, 2
            )


class DebtFundMarket(BaseModel):
    totalFundNumber: int
    numberOfRising: int
    risingPercentage: float = Field(0.0)
    numberOfDowning: int
    downingPercentage: float = Field(0.0)
    risingAndDowningRatio: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.risingPercentage = round(
            100 * (self.numberOfRising / self.totalFundNumber), 2
        )
        self.downingPercentage = round(
            100 * (self.numberOfDowning / self.totalFundNumber), 2
        )
        if self.numberOfDowning <= 0:
            self.risingAndDowningRatio = REPORT_BIGGEST_RATIO
        else:
            self.risingAndDowningRatio = round(
                self.numberOfRising / self.numberOfDowning, 2
            )


class TotalFundMarket(BaseModel):
    totalFundNumber: int
    numberOfRising: int
    numberOfDowning: int
    numberOfRisingOverOnePercent: float
    numberOfDowningOverOnePercent: float


class Index(BaseModel):
    preClose: float
    openPrice: float
    closePrice: float
    navChange: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.navChange = round(
            100 * (self.closePrice - self.openPrice) / self.openPrice, 2
        )


class DailyData(BaseModel):
    date: date
    nifty50: Index
    sensex50: Index
    equityFundMarket: EquityFundMarket
    debtFundMarket: DebtFundMarket
    totalFundMarket: TotalFundMarket
    topRisingFunds: Optional[List[TopRisingFund]]

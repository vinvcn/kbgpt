from datetime import date
from typing import List

from pydantic import BaseModel, Field

from kbgpt.lib.templates.constants import REPORT_BIGGEST_RATIO


class TopRisingFund(BaseModel):
    isin: str
    name: str
    navChange: float


class EquityFundMarket(BaseModel):
    numberOfRising: int
    numberOfDowning: int
    risingAndDowningRatio: float = Field(0.0)
    numberOfRisingOverOnePercent: int
    numberOfDowningOverOnePercent: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.numberOfDowning <= 0:
            self.risingAndDowningRatio = REPORT_BIGGEST_RATIO
        else:
            self.risingAndDowningRatio = round(
                self.numberOfRising / self.numberOfDowning, 4
            )


class DebtFundMarket(BaseModel):
    numberOfRising: int
    numberOfDowning: int
    risingAndDowningRatio: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.numberOfDowning <= 0:
            self.risingAndDowningRatio = REPORT_BIGGEST_RATIO
        else:
            self.risingAndDowningRatio = round(
                self.numberOfRising / self.numberOfDowning, 4
            )


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
    topRisingFunds: List[TopRisingFund]




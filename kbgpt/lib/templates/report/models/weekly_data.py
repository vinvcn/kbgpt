from datetime import date
from typing import List

from pydantic import BaseModel, Field

from .daily_data import Index


class SectorsIndex(BaseModel):
    sectorName: str
    openAum: float
    closeAum: float
    aumChange: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aumChange = round(100 * (self.closeAum - self.openAum) / self.openAum, 4)


class EquityFundMarket(BaseModel):
    avgReturn: float
    numberOfRising: int
    risingPercentage: float = Field(0.0)
    numberOfDowning: int
    downingPercentage: float = Field(0.0)
    numberOfRisingOverFivePercent: int
    topRisingIsin: str
    topRisingFundName: str
    topRisingChange: float

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        divisor = sum([self.numberOfRising, self.numberOfDowning])
        self.risingPercentage = round(100 * self.numberOfRising / divisor, 4)
        self.downingPercentage = round(100 * self.numberOfDowning / divisor, 4)


class DebtFundMarket(BaseModel):
    avgReturn: float
    numberOfRising: int
    numberOfDowning: int
    fundsRoseVSFundsFell: str = Field("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fundsRoseVSFundsFell = f"{self.numberOfRising}:{self.numberOfDowning}"


class FundInfo(BaseModel):
    isin: str
    name: str
    navChange: float


class WeeklyData(BaseModel):
    startTradeDate: date
    endTradeDate: date
    nifty50: Index
    sensex50: Index
    weekLyOpenAum: float
    weekLyCloseAum: float
    weekLyAumChange: float = Field(0.0)
    weekLyCapitalFlow: float = Field(0.0)
    risingSectors: SectorsIndex
    downingSectors: SectorsIndex
    equityFundMarket: EquityFundMarket
    debtFundMarket: DebtFundMarket
    topRisingFunds: List[FundInfo]
    topDowningFunds: List[FundInfo]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weekLyCapitalFlow = (self.weekLyCloseAum - self.weekLyOpenAum) / 1000000000
        self.weekLyAumChange = round(
            100 * (self.weekLyCloseAum - self.weekLyOpenAum) / self.weekLyOpenAum, 4
        )

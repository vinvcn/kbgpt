from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from kbgpt.lib.templates.constants import REPORT_BIGGEST_RATIO


class MonthlyChangeMarket(BaseModel):
    firstSector: Optional[str]
    firstSectorChange: float = Field(0.0)
    tenthFundChange: float = Field(0.0)
    secondSector: Optional[str]
    secondSectorChange: float = Field(0.0)
    lastSector: Optional[str]
    lastSectorChange: float = Field(0.0)
    secondLastSector: Optional[str]
    secondLastSectorChange: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.firstSectorChange = round(self.firstSectorChange, 2)
        self.tenthFundChange = round(self.tenthFundChange, 2)
        self.secondSectorChange = round(self.secondSectorChange, 2)
        self.lastSectorChange = round(self.lastSectorChange, 2)
        self.secondLastSectorChange = round(self.secondLastSectorChange, 2)


class MonthlyAum(BaseModel):
    currentMonth: int = Field(0)
    lastMonth: int = Field(0)
    diff: int = Field(0)
    diffPercent: float = Field(0.0)
    trend: int = Field(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diff = self.currentMonth - self.lastMonth
        if self.lastMonth == 0:
            self.diffPercent = REPORT_BIGGEST_RATIO
        else:
            self.diffPercent = self.diff / self.lastMonth
            self.diffPercent = round(100 * self.diffPercent, 2)
        self.trend = (
            0
            if self.currentMonth == self.lastMonth
            else 1
            if self.currentMonth > self.lastMonth
            else -1
        )


class TopDrivingSector(BaseModel):
    name: Optional[str]
    currentMonth: int = Field(0)
    lastMonth: int = Field(0)
    diff: int = Field(0)
    trend: int = Field(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diff = self.currentMonth - self.lastMonth
        if self.diff == 0:
            self.trend = 0
        elif self.diff > 0:
            self.trend = 1
        else:
            self.trend = -1


class MonthlyAumMarket(BaseModel):
    totalFundNumber: int = Field(0)
    total: MonthlyAum
    equity: MonthlyAum
    debt: MonthlyAum
    topRisingSector: Optional[TopDrivingSector]
    topRisingContrib: float = Field(0.0)
    topDowningSector: Optional[TopDrivingSector]
    topDowningContrib: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.total.diff == 0:
            self.topRisingContrib = REPORT_BIGGEST_RATIO
            self.topDowningContrib = REPORT_BIGGEST_RATIO
        else:
            self.topRisingContrib = self.topRisingSector.diff / self.total.diff
            self.topRisingContrib = round(100 * self.topRisingContrib, 2)
            self.topDowningContrib = self.topDowningSector.diff / self.total.diff
            self.topDowningContrib = round(100 * self.topDowningContrib, 2)


class Fund(BaseModel):
    fundName: str
    releaseDate: date
    className: str


class MonthlyNFOInfo(BaseModel):
    total: MonthlyAum
    equity: MonthlyAum
    debt: MonthlyAum
    nextMonthNFOInfo: Optional[List[Fund]]

    class Config:
        arbitrary_types_allowed = True


class MonthlyData(BaseModel):
    date: date
    monthlyChangeMarket: MonthlyChangeMarket
    monthlyAumMarket: MonthlyAumMarket
    monthlyNFOInfo: MonthlyNFOInfo

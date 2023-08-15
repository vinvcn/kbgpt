import enum
from datetime import date
from math import ceil
from typing import List, Optional, Tuple

from dateutil import relativedelta
from pydantic import BaseModel, Field

from kbgpt.lib.templates.constants import REPORT_BIGGEST_RATIO

from .utils import round  # pylint: disable=redefined-builtin

# pylint: disable = invalid-name


class Unit(enum.Enum):
    MILLION = 0
    CRORE = 1
    YI = 2
    BILLION = 3
    BAIYI = 4
    QIANYI = 5
    TRILLION = 6


class UnitStr(enum.Enum):
    CRORE = "Cr."
    BILLION = "bn"
    TRILLION = "tn"


class MonthlyChangeMarket(BaseModel):
    firstSector: Optional[str]
    firstSectorChange: float = Field(0.0)
    tenthFundChange: Optional[Optional[float]]
    secondSector: Optional[str]
    secondSectorChange: float = Field(0.0)
    lastSector: Optional[str]
    lastSectorChange: float = Field(0.0)
    secondLastSector: Optional[str]
    secondLastSectorChange: float = Field(0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.firstSectorChange = round(self.firstSectorChange, 2)
        if self.tenthFundChange:
            self.tenthFundChange = round(self.tenthFundChange, 2)
        self.secondSectorChange = round(self.secondSectorChange, 2)
        self.lastSectorChange = round(self.lastSectorChange, 2)
        self.secondLastSectorChange = round(self.secondLastSectorChange, 2)


class MonthlyAum(BaseModel):
    currentMonth: float = Field(0)
    lastMonth: float = Field(0)
    diff: float = Field(0)
    diffPercent: float = Field(0.0)
    trend: int = Field(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currentMonth = round(self.currentMonth, 2)
        self.lastMonth = round(self.lastMonth, 2)
        self.diff = self.currentMonth - self.lastMonth
        self.diff = round(self.diff, 2)
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
    currentMonth: float = Field(0)
    currentMonthStr: str = Field("")
    currentMonthUnitStr: str = Field("")
    currentMonthUnitName: str = Field("")
    lastMonth: float = Field(0)
    diff: float = Field(0)
    diffStr: str = Field("")
    diffUnitStr: str = Field("")
    diffUnitName: str = Field("")
    trend: int = Field(0)

    @staticmethod
    def to_str_wiz_unit(val: float) -> Tuple[str, str]:
        int_len = len(str(int(val)))

        if Unit.MILLION.value <= int_len < Unit.BILLION.value:
            return str(val), UnitStr.CRORE.name.lower(), UnitStr.CRORE.value
        elif Unit.BILLION.value <= int_len < Unit.TRILLION.value:
            return (
                round(val / 100, 2),
                UnitStr.BILLION.name.lower(),
                UnitStr.BILLION.value,
            )
        else:
            return (
                round(val / 1000, 2),
                UnitStr.TRILLION.name.lower(),
                UnitStr.TRILLION.value,
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currentMonth = round(self.currentMonth, 2)
        (
            self.currentMonthStr,
            self.currentMonthUnitName,
            self.currentMonthUnitStr,
        ) = self.to_str_wiz_unit(self.currentMonth)
        self.lastMonth = round(self.lastMonth, 2)
        self.diff = self.currentMonth - self.lastMonth
        self.diff = round(self.diff, 2)
        self.diffStr, self.diffUnitName, self.diffUnitStr = self.to_str_wiz_unit(
            self.diff
        )
        self.trend = (
            0
            if self.currentMonth == self.lastMonth
            else 1
            if self.currentMonth > self.lastMonth
            else -1
        )


class MonthlyAumMarket(BaseModel):
    totalFundNumber: int = Field(0)
    total: MonthlyAum
    equity: MonthlyAum
    debt: MonthlyAum
    topRisingSector: Optional[TopDrivingSector]
    topRisingContrib: float = Field(0.0)  #
    topRisingContribStr: Optional[str]
    topDowningSector: Optional[TopDrivingSector]
    topDowningContrib: float = Field(0.0)  #
    topDowningContribStr: Optional[str]
    contraryFlowStr: Optional[str]
    contraryTopContribStr: str = Field("")
    contraryDownContribStr: str = Field("")

    @staticmethod
    def round_contrib(value: float):
        """round contribution"""
        neg = value < 0
        return (
            0.1
            if 0 < value <= 0.1
            else -0.1
            if -0.1 <= value < 0
            else -ceil(abs(value))
            if neg
            else ceil(abs(value))
            if value != 0
            else 0
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.total.diff == 0:
            self.topRisingContrib = REPORT_BIGGEST_RATIO
            self.topRisingContribStr = ""
            self.topDowningContrib = REPORT_BIGGEST_RATIO
            self.topDowningContribStr = ""
        else:
            self.topRisingContrib = self.topRisingSector.diff / self.total.diff
            self.topRisingContrib = self.round_contrib(100 * self.topRisingContrib)
            self.topRisingContribStr = f"or {self.topRisingContrib}%"
            self.topDowningContrib = self.topDowningSector.diff / self.total.diff
            self.topDowningContrib = self.round_contrib(100 * self.topDowningContrib)
            self.topDowningContribStr = f"or {self.topDowningContrib}%"

        if self.total.trend >= 0:
            # if total aum increase and top downing dropping
            self.contraryFlowStr = (
                "most outflow" if self.topDowningSector.trend < 0 else "least inflow"
            )
            self.contraryDownContribStr = (
                ""
                if self.total.diff == 0 or self.topDowningSector.trend <= 0
                else f"or {self.topDowningContrib}%"
            )

        else:
            # if total aum drop and top rising go up
            self.contraryFlowStr = (
                "most inflow" if self.topRisingSector.trend > 0 else "least outflow"
            )
            self.contraryTopContribStr = (
                ""
                if self.total.diff == 0 or self.topRisingSector.trend >= 0
                else f"or {self.topRisingContrib}%"
            )


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
    month_str: Optional[str]
    nextMonthStr: Optional[str]
    monthlyChangeMarket: MonthlyChangeMarket
    monthlyAumMarket: MonthlyAumMarket
    monthlyNFOInfo: MonthlyNFOInfo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.month_str = self.date.strftime("%B")
        self.nextMonthStr = (
            self.date + relativedelta.relativedelta(months=1)
        ).strftime("%B")

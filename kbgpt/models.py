"""
models
"""
from typing import List

from pydantic import BaseModel


class EquityFundsRiseCount(BaseModel):
    """
    Represents the count of equity funds that rose in value.

    Attributes:
        total (int): The total number of equity funds.
        more_than_1_percentage (int): The number of equity funds with a rise of more than 1%.
    """
    total: int
    more_than_1_percentage: int

class EquityFundsFellCount(BaseModel):
    """
    Represents the count of equity funds that fell in value.

    Attributes:
        total (int): The total number of equity funds.
        more_than_1 (int): The number of equity funds with a fall of more than 1%.
        more_than_1_percentage (int): The percentage of equity funds with a fall of more than 1%.
    """
    total: int
    more_than_1: int
    more_than_1_percentage: int

class EquityFundsMarket(BaseModel):
    """
    Represents the market performance of equity funds.

    Attributes:
        rise_count (EquityFundsRiseCount): The count of equity funds that rose in value.
        fell_count (EquityFundsFellCount): The count of equity funds that fell in value.
    """
    rise_count: EquityFundsRiseCount
    fell_count: EquityFundsFellCount

class Index(BaseModel):
    """
    Represents an index.

    Attributes:
        open (float): The opening value of the index.
        close (float): The closing value of the index.
        trend_percentage (float): The percentage change of the index.
    """
    open: float
    close: float
    trend_percentage: float

class DebtFundsPerformed(BaseModel):
    """
    Represents the performance of debt funds.

    Attributes:
        rise_count (int): The number of debt funds that rose in value.
        fell_count (int): The number of debt funds that fell in value.
    """
    rise_count: int
    fell_count: int

class Top5Funds(BaseModel):
    """
    Represents the top 5 funds.

    Attributes:
        name (str): The name of the fund.
        percentage (int): The percentage change of the fund.
    """
    name: str
    percentage: int

class DailyData(BaseModel):
    """
    Represents daily market data.

    Attributes:
        date (str): The date of the data.
        nifty50 (Index): The performance of Nifty 50 index.
        sensex50 (Index): The performance of Sensex 50 index.
        equity_funds_market (EquityFundsMarket): The market performance of equity funds.
        debt_funds_performed (DebtFundsPerformed): The performance of debt funds.
        top_5_funds (List[Top5Funds]): The top 5 funds.
    """
    date: str
    nifty50: Index
    sensex50: Index
    equity_funds_market: EquityFundsMarket
    debt_funds_performed: DebtFundsPerformed
    top_5_funds: List[Top5Funds]


# Example usage:
data_dict = {
    "date": "July 05, 2023",
    "nifty50": {
        "open": 100,
        "close": 99,
        "trend_percentage": 1,
    },
    "sensex50": {
        "open": 1000,
        "close": 1100,
        "trend_percentage": 10,
    },
    "equity_funds_market": {
        "rise_count": {
            "total": 20,
            "more_than_1_percentage": 50
        },
        "fell_count": {
            "total": 40,
            "more_than_1": 40,
            "more_than_1_percentage": 100
        },
    },
    "debt_funds_performed": {
        "rise_count": 12,
        "fell_count": 33
    },
    "top_5_funds": [
        {
            "name": "ABC1",
            "percentage": 3
        },
        {
            "name": "ABC2",
            "percentage": 5
        },
        {
            "name": "ABC3",
            "percentage": 6
        },
        {
            "name": "ABC4",
            "percentage": 7
        },
        {
            "name": "ABC5",
            "percentage": 8
        }, 
    ]
}

data_model = Data(**data_dict)


print(data_model.json(indent=4))

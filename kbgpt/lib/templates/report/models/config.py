from datetime import date

from pydantic import BaseModel


class Index(BaseModel):
    entry_key: str
    window_size_in_day: int


class FundType(BaseModel):
    entry_key: str
    window_size_in_day: int


class TopFunds(BaseModel):
    entry_key: str
    info_key: str
    window_size_in_day: int


class DailyReportModel(BaseModel):
    nifty50_index_stats: Index
    sensex50_index_stats: Index
    equity_fund_stats: FundType
    debts_fund_stats: FundType
    top_fund_stats: TopFunds

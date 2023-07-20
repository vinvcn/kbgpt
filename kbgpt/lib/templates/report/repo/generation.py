from pydantic import BaseModel

from kbgpt.lib.templates.report.models.config import FundType, Index, TopFunds


class Daily(BaseModel):
    """daily report configs"""

    NIFTY50 = Index(entry_key="kline:day:bfq:NSE-Nifty 50 Index", window_size_in_day=1)

    SENSEX50 = Index(entry_key="kline:day:bfq:NSE-S&P BSE SENSEX 50 Index", window_size_in_day=1)

    EQUITY = FundType(entry_key="market-data-crawling-service:fund:ranking:navchange:Equity", window_size_in_day=1)

    DEBT = FundType(entry_key="market-data-crawling-service:fund:ranking:navchange:Debt", window_size_in_day=1)

    TOP_5 = TopFunds(
        entry_key="market-data-crawling-service:fund:ranking:navchange:All",
        info_key="market-data-crawling-service:fund:info:base",
        window_size_in_day=1,
    )


DAILY = Daily()


def daily_to_json():
    """ dump daily config to json """
    print(DAILY.json(indent=4))


if __name__ == "__main__":
    daily_to_json()

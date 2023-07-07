""" weekly report template """
TEMPLATE = """
Fill the following data into the parenthesis of the content below.

Data:
```json
{
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
            "more_than_1%": 10,
            "more_than_1%_percentage": 50
        },
        "fell": {
            "total": 40,
            "more_than_1": 40,
            "more_than_1%_percentage": 100
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

```


---
Content:
Summary of today's Mutual Fund Market

As of the close on (day), (date): Nifty 50 opened at (xx), closed (up/down) (xxx%) at (xxx). Sensex50 started at (xxx), (gained/loss) (xx%) to end at (xxx).

Given the performance of the stock market, the equity funds market performed (strongly/well/adequately/weakly/pessimistically). There were (xxx) funds that rose today, took (xx%) of the equity fund market, and (xx) of which increased by more than 1%. Concurrently, (xxx) or (xx%) funds fell, with (xx) decreased by more than 1%.

Compare to equity fund market, debt funds performed (strongly/well/adequately/weakly/pessimistically), with (xxx) funds rising today and (xxx) funds falling.

Here are the top 5 funds today:

(fund name)(+ percentage),

(fund name)(+percentage),

(fund name)(+percentage),

(fund name)(+percentage) and

(fund name)(+percentage).

"""

KEYWORDS = []
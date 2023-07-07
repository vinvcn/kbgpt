
TEMPLATE = """
Fill the following data into the parenthesis of the content below.

Data:
```json
{
    "date_from": "July 4, 2023",
    "date_to": "July 10, 2023",
    "nifty_50": {
        "trending_percentage": -10,
        "close": 1111
    },
    "sensex_50": {
        "rending_percentage": 10,
        "close": 2222
    },
    "performance": "negative",
    "aum": {
        "total": 213322,
        "trending_percentage": -12
    },
    "sectors": {
        "top_rise": {
            "sector_name":"luckystory",
            "aum": 3333,
            "aum_percentage": 20
        },
        "top_fell": {
            "sector_name":"otherstory",
            "aum": 4444,
            "aum_percentage": 10
        }
    }
    "equity_funds":{
        "avg_return_percenage": 2,
        "rise_counts": 33,
        "rose_fund_percentage": 22,
        "fell_counts": 40,
        "fell_fund_percentage": 15,
        "rose_more_than_5%_counts": 2,
        "highest_gain_fund": "ABSL",
        "highest_gain_percentage": 10
    },
    "debt_funds": {
        "avg_return_percenage": 2,
        "rise_counts": 33,
        "fell_counts": 40,
        "ratio_of_rise_and_fell": "33:44"
    },
    "top_5_funds":[
        {
            "name": "ABC1",
            "percentage": "3"
        },
        {
            "name": "ABC2",
            "percentage": "5"
        },
        {
            "name": "ABC3",
            "percentage": "6"
        },
        {
            "name": "ABC4",
            "percentage": "7"
        },
        {
            "name": "ABC5",
            "percentage": "8"
        }],
    "worst_5_funds": [
        {
            "name": "DEF1",
            "percentage": -1
        },
        {
            "name": "DEF2",
            "percentage": -2
        },
        {
            "name": "DEF3",
            "percentage": -3
        },
        {
            "name": "DEF4",
            "percentage": -4
        },
        {
            "name": "DEF5",
            "percentage": -5
        }
    ]
}
```

Content:

Weekly Summary of Mutual Fund Market

During this week (date to date), Nifty 50 closed (up/down) xxx% at xx. Sensex50 (gained/loss) (xx%) to end at (xxx). As the reaction to stock market, the India fund market witnessed a (positive/negative) performance in the week.

In the meanwhile, the assets under management (AUM) of the mutual fund industry for this week stood at (Rs. xxx), registering a (growth/decrease) of (percentage).

The (growth/negative growth) in AUM was driven by the (sector name). (sector name) contributed (Rs. Xxx) or (percentage) of the total industry AUM. On the contrary, the AUM of (sector name) (outflowed/inflowed) the most, stood at (Rs. xxx) or (percentage) of the total industry AUM.

Let's dive deeper into sectors.

1. Equity Funds

This week, the average return of equity funds was (xx%). There were (xxx) funds end with positive returns this week, took (xx%) of the equity fund market. Concurrently, (xxx) or (xx%) funds recorded negative returns.

There were (xx) equity funds with an increase of more than 5% this week. And the winner of highest gain was {name}, with an increase of xx%.

2. Debt Funds

The average return of debt funds this week was (xx%). The number of debt funds that rose this week was (xx), while the number of fell was (xx). The ratio of funds rose VS funds fell was (xx:xx).

Lastly, here is the top 5 mutual funds of this week:

(fund name)(+ percentage),

(fund name)(+ percentage),

(fund name)(+ percentage),

(fund name)(+ percentage) and

(fund name)(+ percentage).

And 5 worst performance funds:

(fund name)(- percentage),

(fund name)(- percentage),

(fund name)(- percentage),

(fund name)(- percentage) and

(fund name)(- percentage).
"""
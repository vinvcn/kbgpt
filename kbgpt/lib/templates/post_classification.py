INFORMATION = "INFORMATION"
GREETINGS = "GREETINGS"
MEANINGLESS = "MEANINGLESS"
POLITICAL = "POLITICAL"
HARMFUL = "HARMFUL"
OFFENSIVE = "OFFENSIVE"
OTHERS = "OTHERS"
CATEGORIES = [
    INFORMATION, GREETINGS, MEANINGLESS, HARMFUL, OFFENSIVE, POLITICAL, OTHERS
]
CLASSFIER_TEMPLATE = f"""
    You are a maintainer of a internet forum, your job is to classify posts into categories. 
    The categories are: {", ".join(CATEGORIES)}
    Example:
    1. Microeconomics is based on models of consumers or firms (which economists call agents) that make decisions about what to buy, sell, or produce—with the assumption that those decisions result in perfect market clearing (demand equals supply) and other ideal conditions.
    {INFORMATION}
    2. Microeconomics is aliens.
    {MEANINGLESS}
    3. I hate China
    {OFFENSIVE}
    4. hi everyone
    {GREETINGS}
    Here is the Post:
    {{title}}
    {{content}}
"""

CATEGORY_TO_IGNORE = [HARMFUL, OFFENSIVE, POLITICAL]

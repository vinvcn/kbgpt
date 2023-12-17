from datetime import datetime
from os import name

from pandas import describe_option
from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import UtilityMixin


class MutualFund(UtilityMixin, Base):
    """mutual fund"""

    __tablename__ = "mf_mutual_fund"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(
        String(128, collation="utf8mb4_unicode_ci"),
        comment="the name of the mutual fund",
    )
    isin = Column(String(128, collation="utf8mb4_unicode_ci"), comment="the isin")
    description = Column(
        Text(collation="utf8mb4_unicode_ci"),
        comment="the description of the mutual fund",
    )
    created_at = Column(
        DateTime, default=datetime.utcnow, comment="the creation time of the row"
    )
    updated_at = Column(
        DateTime, default=datetime.utcnow, comment="the update time of the row"
    )


class NewsArticle(UtilityMixin, Base):
    """news article"""

    __tablename__ = "mf_news_article"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mf_id = Column(Integer, comment="the id of the fund this belongs to")
    title = Column(String(128, collation="utf8mb4_unicode_ci"))
    source = Column(String(128, collation="utf8mb4_unicode_ci"))
    word_count = Column(Integer, default=0)
    tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    summary = Column(
        Text(collation="utf8mb4_unicode_ci"), comment="the summary of the news article"
    )
    content = Column(
        Text(collation="utf8mb4_unicode_ci"), comment="the content of the news article"
    )
    orig_url = Column(
        String(256, collation="utf8mb4_unicode_ci"),
        comment="the original url of the article",
    )
    timestamp = Column(DateTime, comment="the time when the article was written.")
    orig_url_index = Index("orig_url_index", orig_url)


class MFChatGPTReport(UtilityMixin, Base):
    """chat gpt generated news report"""

    __tablename__ = "mf_news_chatgpt_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, comment="related news id")
    mf_id = Column(Integer, comment="the id of the fund this belongs to")
    word_count = Column(Integer, default=0)
    tokens = Column(Integer, default=0)
    content = Column(Text(collation="utf8mb4_unicode_ci"))
    timestamp = Column(DateTime, comment="the time when the report was generated.")

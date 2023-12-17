import abc
import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, Dict

import aiohttp
import sqlalchemy
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from serpapi import GoogleSearch
from sqlalchemy.orm import sessionmaker

from kbgpt.lib.db.mysql.mutual_funds import NewsArticle
from kbgpt.lib.exec.engines.configs.models import MFSearchMod
from kbgpt.lib.exec.engines.engine import Engine


class MFSearch(Engine):
    def __init__(self, mod: MFSearchMod) -> None:
        super().__init__(mod)
        self.engine = sqlalchemy.create_engine(mod.connection_string, echo=False)

    @abc.abstractmethod
    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        assert "fund_name" in kwargs, "fund_name must be present in argument list"
        assert "fund_id" in kwargs, "fund_id must be present in argument list"

        config: MFSearchMod = self.config
        params = {
            "q": kwargs["fund_name"],
            "location": "Mumbai, Maharashtra, India",
            "device": "desktop",
            "hl": "en",
            "gl": "in",
            "google_domain": "google.co.in",
            "num": "10",
            "api_key": config.serpapi_key,
            "tbm": "nws",
            "output": "json",
        }
        search = GoogleSearch(params)
        serpapi_rst = search.get_dict()
        articles = await asyncio.gather(
            [self.crawlink(rst_obj, kwargs["fund_id"]) for rst_obj in serpapi_rst],
            return_exceptions=False,
        )
        for arti in articles:
            if arti and len(arti.content < 2000):
                return arti.content

        return "N/A"

    async def crawlink(self, serapi_article_obj, fund_id: int):
        news_url = serapi_article_obj["link"]
        publish_date = await self.parse_publish_date(serapi_article_obj["date"])
        html_page = await self.fetch_html_page(news_url)
        soup = BeautifulSoup(html_page, "html.parser")
        text_content = soup.get_text("\n")
        refined_text = self.refine_raw_html_texts(text_content)
        news_article = NewsArticle(
            title=serapi_article_obj["title"],
            mf_id=fund_id,
            source=serapi_article_obj["source"],
            word_count=len(text_content.split()),
            content=refined_text,
            orig_url=news_url,
            timestamp=publish_date,
        )
        return news_article

    async def fetch_html_page(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()

    async def save_news_article(self, news_article: NewsArticle):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            session.add(news_article)
            session.commit()

    async def is_news_url_already_exist(self, news_url):
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            result = (
                session.query(NewsArticle.orig_url)
                .filter(NewsArticle.orig_url == news_url)
                .order_by(NewsArticle.timestamp.desc())
                .first()
            )
            return result

    async def parse_publish_date(self, raw_publish_date):
        publish_date = None
        try:
            raw_publish_date = raw_publish_date.replace("Sept", "Sep")
            publish_date = datetime.strptime(raw_publish_date, "%d-%b-%Y")
        except ValueError as ex:
            time_now = datetime.utcnow()
            scalar = re.findall(r"\d+", raw_publish_date)[0]
            scalar = int(scalar)

            if "sec" in raw_publish_date:
                publish_date = time_now - timedelta(seconds=scalar)
            elif "min" in raw_publish_date:
                publish_date = time_now - timedelta(minutes=scalar)
            elif "hour" in raw_publish_date:
                publish_date = time_now - timedelta(hours=scalar)
            elif "day" in raw_publish_date:
                publish_date = time_now - timedelta(days=scalar)
            elif "month" in raw_publish_date:
                publish_date = time_now - relativedelta(months=scalar)
            else:
                raise ValueError("failed to parse date for the article") from ex

        return publish_date

    def refine_raw_html_texts(self, html_texts):
        non_empty_lines = [ln.strip() for ln in html_texts.split("\n") if ln.strip()]
        pat = r"\b\w+\b"
        more_than_three_words = [
            ln for ln in non_empty_lines if len(re.findall(pat, ln)) > 3
        ]
        return "\n".join(more_than_three_words)

import json
import logging
from json.decoder import JSONDecodeError

import openai
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

from config import profile
from kbgpt.api.senti.models import Sentiment, SentimentResponse
from kbgpt.lib.db.mysql.sentiment_record import SentimentRecord
from kbgpt.lib.logging import alog
from kbgpt.lib.templates.engine import SimpleEngine
from kbgpt.svc.aigc import Agent
from kbgpt.svc.utils.openai import get_total_cost


class SentimentAgent(Agent):
    """sentiment analysis agent"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.engine = SimpleEngine(name="sentiment")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        retry=retry_if_exception_type(JSONDecodeError),
        reraise=True
    )
    @alog(SentimentRecord)
    async def analyze(self, req: Sentiment) -> SentimentResponse:
        """analyze the sentiment according to the request"""

        prompt = await self.engine.agenerate(**req.dict())
        completion = await openai.ChatCompletion.acreate(
            model=profile.sentiment.analysis_model,
            messages=[{"role": "user", "content": prompt}],
        )

        promp_tokens = completion["usage"]["prompt_tokens"]
        comp_tokens = completion["usage"]["completion_tokens"]
        total_tokens = completion["usage"]["total_tokens"]
        cost = get_total_cost(
            profile.comment.generative_model, promp_tokens, comp_tokens
        )
        content:str = completion.choices[0].message["content"]
        obj = json.loads(content)
        logging.info("got result:")
        logging.info(obj)

        return SentimentResponse(
            level=obj["level"],
            description=obj["description"],
            prompt_tokens=promp_tokens,
            comp_tokens=comp_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )

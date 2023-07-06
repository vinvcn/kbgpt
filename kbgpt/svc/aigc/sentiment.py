import openai

from config import profile
from kbgpt.api.senti.models import Sentiment, SentimentResponse
from kbgpt.lib.db.mysql.sentiment_record import SentimentRecord
from kbgpt.lib.logging import alog
from kbgpt.lib.templates.engine import SimpleEngine
from kbgpt.svc.utils.openai import get_total_cost


class SentimentAgent:
    """ sentiment analysis agent """

    def __init__(self) -> None:
        super().__init__()
        self.engine = SimpleEngine(name="sentiment")

    @alog(SentimentRecord)
    async def analyze(self, req: Sentiment) -> SentimentResponse:
        """ analyze the sentiment according to the request """

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
        content = completion.choices[0].message["content"]
        split = [s for s in content.split("\n") if s]

        return SentimentResponse(
            level=split[0],
            description=split[1],
            prompt_tokens=promp_tokens,
            comp_tokens=comp_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )

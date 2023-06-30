import logging
from typing import Tuple

from langchain.callbacks import OpenAICallbackHandler
from sanic import Sanic

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql.qa_record import QARecord
from kbgpt.lib.logging import alog
from kbgpt.svc.qa_services import AbstractAgent


class ProxiedQAAgent:
    """
    Proxy agent for the QA logic
    """

    def __init__(self, app:Sanic, agent: AbstractAgent) -> None:
        self.agent = agent
        self.app = app

    def _create_result(self, ans: str, stats: OpenAICallbackHandler, cached: bool):
        """
        Create the result
        """
        return {
            "success": True,
            "answer": ans,
            "total_tokens": stats.total_tokens,
            "total_cost": stats.total_cost,
            "prompt_tokens": stats.prompt_tokens,
            "completion_tokens": stats.completion_tokens,
            "successful_requests": stats.successful_requests,
            "hit_cache": cached,
        }

    async def _answer_question_with_cache(
        self, question: str, **kwargs
    ) -> Tuple[str, OpenAICallbackHandler, bool]:
        cache:RedisCacheStoreStrategy = self.app.ctx.redicache
        cached = None
        try:
            cached = await cache.retrieve(query=question)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error("exception while fetching cache for question %s", question)
            logging.exception(e)
            logging.warning(
                "this should not stop normal process, continue without cache"
            )

        if cached:
            return self._create_result(
                cached.metadata.answer, OpenAICallbackHandler(), True
            )
        else:
            ans, stats = await self.agent.answer_question(question=question, **kwargs)
            try:
                # try write to cache
                await cache.write_to_store(question=question, answer=ans)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logging.error(
                    "exception while writing to store for question %s",
                    question,
                )
                logging.exception(e)
            return self._create_result(ans, stats, False)

    @alog(QARecord)
    async def answer_question(
        self, question: str, streaming: bool = False, callbacks=None
    ) -> Tuple[str, OpenAICallbackHandler, bool]:
        """
        Answer a question as a customer service agent
        """
        question = question.strip()
        cache:RedisCacheStoreStrategy = self.app.ctx.redicache
        if len(question) == 0:
            raise ValueError(f"Empty question {question} provided")
        if not profile.cache.use_redis_cache or not cache.is_cache_valid():
            # if not using redis cache or cache is not valid
            ans, stats = await self.agent.answer_question(
                question=question, streaming=streaming, callbacks=callbacks
            )
            return self._create_result(ans, stats, False)
        else:
            return await self._answer_question_with_cache(
                question=question, streaming=streaming, callbacks=callbacks
            )

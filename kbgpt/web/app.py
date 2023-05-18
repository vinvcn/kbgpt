"""
define the Sanic app
"""
import logging
import time
import uuid
from json import dumps
from typing import Tuple

from aiofiles import open as aopen
from aiofiles import tempfile
from langchain.callbacks import OpenAICallbackHandler
from sanic import Sanic
from sanic.response import json
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from tenacity import retry, stop_after_attempt, wait_fixed

from config import profile
from kbgpt.lib.db import CacheWarmingUpException
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.svc.file_services import add_files_to_customer_service
from kbgpt.svc.qa_services import AbstractAgent, ConvAgent, QAagent
from kbgpt.web.callbacks import StreamingTextCallbackHandler

app = Sanic(profile.sanic.app_name)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def warmup_task():
    """
    kick off warm up task
    """
    cache = RedisCacheStoreStrategy.get_instance()
    try:
        await cache.refresh_cache()
    except CacheWarmingUpException as e:
        logging.exception(e)
        logging.warning("cache warming up in another task, aborting")


@app.route("/process_file", methods=["POST"])
async def process_file(request):
    """
    POST endpoint to process file"""
    # pylint: disable=broad-except
    try:
        async with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for file in request.files["file"]:
                if len(file.body) <= 0:
                    raise ValueError(f"File {file.name} can not be empty")
                path = f"{temp_dir}/{file.name}"
                logging.debug("writing to temp file %s", path)
                async with aopen(path, "wb") as f:
                    await f.write(file.body)
                    await f.flush()
                    paths.append(path)

            logging.info(
                "adding files to customer service %s\n", "\n".join(paths)
            )
            await add_files_to_customer_service(paths, flush_index=True)
        app.add_task(warmup_task())

        return json({"success": True})
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})


@app.route("/get_qa", methods=["GET", "POST"])
async def answer_question_get(request):
    """
    GET endpoint to answer a question"""
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        question = request.json["question"]
        logging.info("handling request: \n%s", dumps(request.json, indent=4))
        agent = ProxiedAgent(QAagent.get_instance())
        result = await agent.answer_question(question=question)
        return json(result)
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})
    finally:
        logging.debug(
            "End of answer_question_get request, total time %.3f",
            (time.perf_counter() - start_counter),
        )


# pylint: disable=unused-argument
@app.websocket("/qa")
async def answer_question(request, ws):
    """
    Websocket endpoint to answer a question
    """
    agent = ConvAgent(
        streaming=True, handlers=[StreamingTextCallbackHandler(ws)]
    )
    while True:
        # Wait for incoming message
        message = await ws.recv()
        # Process message as needed
        # processed_message = process_qa_message(message)
        # Send response back over websocket
        answer = await agent.question(message)

        await ws.send(answer)
        # llm_result = await agent.answer_question(question=message)
        # await ws.send(llm_result)


class ProxiedAgent:
    """
    Proxy agent for the real agent
    """

    def __init__(self, agent: AbstractAgent) -> None:
        self.agent = agent

    def _create_result(
        self, ans: str, stats: OpenAICallbackHandler, cached: bool
    ):
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
        self, question: str
    ) -> Tuple[str, OpenAICallbackHandler, bool]:
        cache = RedisCacheStoreStrategy.get_instance()
        cached = None
        try:
            cached = await cache.retrieve(query=question)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error(
                "exception while fetching cache for question %s", question
            )
            logging.exception(e)
            logging.warning(
                "this should not stop normal process, continue without cache"
            )

        if cached:
            return self._create_result(
                cached.metadata.answer, OpenAICallbackHandler(), True
            )
        else:
            ans, stats = await self.agent.answer_question(question=question)
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

    async def answer_question(
        self, question: str
    ) -> Tuple[str, OpenAICallbackHandler, bool]:
        """
        Answer a question as a customer service agent
        """
        question = question.strip()
        cache = RedisCacheStoreStrategy.get_instance()
        if len(question) == 0:
            raise ValueError(f"Empty question {question} provided")
        if not profile.cache.use_redis_cache or not cache.is_cache_valid():
            # if not using redis cache or cache is not valid
            ans, stats = await self.agent.answer_question(question=question)
            return self._create_result(ans, stats, False)
        else:
            return await self._answer_question_with_cache(question=question)


def run():
    """
    run the web app
    """
    app.run(
        host=profile.sanic.ip,
        port=profile.sanic.port,
        debug=profile.sanic.debug,
        workers=profile.sanic.workers,
        protocol=WebSocketProtocol,
    )

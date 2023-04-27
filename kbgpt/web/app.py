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

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.vector_store import get_embeddings
from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import AbstractAgent, ConvAgent, QAagent
from kbgpt.web.callbacks import StreamingTextCallbackHandler

app = Sanic(profile.sanic.app_name)


@app.route("/process_file", methods=["POST"])
async def process_file(request):
    """
    POST endpoint to process file"""
    # pylint: disable=broad-except
    try:
        flush = profile.indexing.flush_before_write
        for file in request.files["file"]:
            if len(file.body) <= 0:
                raise ValueError(f"File {file.name} can not be empty")
            async with tempfile.NamedTemporaryFile(
                delete=True, prefix=str(uuid.uuid4()), suffix=file.name
            ) as temp_file:
                async with aopen(temp_file.name, "wb") as f:
                    await f.write(file.body)
                    await f.flush()
                    await add_file_to_customer_service(
                        path=temp_file.name, flush_index=flush
                    )
                    flush = False
        return json({"success": True})
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})


@app.route("/get_qa", methods=["GET"])
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

    async def answer_question(
        self, question: str
    ) -> Tuple[str, OpenAICallbackHandler, bool]:
        """
        Answer a question as a customer service agent
        """
        if not profile.cache.use_redis_cache:
            ans, stats = await self.agent.answer_question(question=question)
            return self._create_result(ans, stats, False)
        else:
            cache = RedisCacheStoreStrategy.get_instance()
            cached = await cache.retrieve(query=question)
            if cached:
                return self._create_result(
                    cached["answer"], OpenAICallbackHandler(), True
                )
            else:
                ans, stats = await self.agent.answer_question(question=question)
                await cache.write_to_store(question=question, answer=ans)
                return self._create_result(ans, stats, False)


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

"""
define the Sanic app
"""
import logging
import time
from json import dumps
from typing import Tuple, List

from aiofiles import open as aopen
from aiofiles import tempfile
from langchain.callbacks import OpenAICallbackHandler
from redis.exceptions import LockError
from sanic import Request, Sanic
from sanic.response import JSONResponse, json
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from tenacity import retry, stop_after_attempt, wait_fixed

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.svc.comment_service import CommentAgent, Post
from kbgpt.svc.file_services import add_files_to_customer_service
from kbgpt.svc.qa_services import AbstractAgent, QAagent
from kbgpt.web.callbacks import StreamingAsyncHandler
from pydantic import parse_obj_as

app = Sanic(profile.sanic.app_name)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def warmup_task():
    """
    kick off warm up task
    """
    cache = RedisCacheStoreStrategy.get_instance()
    # pylint: disable=broad-except
    try:
        await cache.refresh_cache()
    except LockError as e:
        logging.exception(e)
        logging.warning(
            "aquiring lock failed, another thread might be working aborting"
        )
    except Exception as e:
        logging.exception(e)
        logging.warning("cache refreshing cache encountered exception")
        raise e


@app.route("/warmup_cache", methods=["GET", "POST"])
async def warmup_cache(request):
    """
    trigger warm up task without updating documents
    """
    agent = ProxiedDocAgent()
    return await agent.refresh_cache(sanic_app=app, request=request)


@app.route("/doc_version", methods=["GET"])
async def doc_version(request):  # pylint: disable=unused-argument
    """
    get the doc version and timestamp
    """
    cache = RedisCacheStoreStrategy.get_instance()
    # pylint: disable=broad-except
    try:
        index_version = cache.get_index_version()
        return json(
            {
                "success": True,
                "version": index_version.uuid,
                "timestamp": str(index_version.timestamp),
            }
        )
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})


@app.route("/process_file", methods=["POST"])
async def process_file(request):
    """
    POST endpoint to process file"""
    # pylint: disable=broad-except
    agent = ProxiedDocAgent()
    return await agent.process_file_and_refresh_cache(sanic_app=app, request=request)


@app.route("/get_qa", methods=["GET", "POST"])
async def answer_question_get(request):
    """
    GET endpoint to answer a question"""
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        question = request.json["question"]
        logging.info("handling request: \n%s", dumps(request.json, indent=4))
        agent = ProxiedQAAgent(QAagent.get_instance())
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
@app.route("/stream_qa", methods=["GET", "POST"])
async def answer_question(request: Request):
    """
    Websocket endpoint to answer a question
    """
    headers = {"Cache-Control": "no-cache"}
    response = await request.respond(
        headers=headers, content_type="text/event-stream; charset=utf-8"
    )
    callbacks = [StreamingAsyncHandler(response.send)]
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        question = request.json["question"]
        logging.info("handling request: \n%s", dumps(request.json, indent=4))
        agent = ProxiedQAAgent(QAagent.get_instance())
        result = await agent.answer_question(
            question=question, streaming=True, callbacks=callbacks
        )
        await response.send(f"data: {dumps(result)}")
    except Exception as e:
        logging.exception(e)
        obj = {"success": False, "error": str(e)}
        await response.send(f"data: {dumps(obj=obj)}")
    finally:
        await response.eof()
        logging.debug(
            "End of answer_question_get request, total time %.3f",
            (time.perf_counter() - start_counter),
        )


@app.route("/get_comments", methods=["GET", "POST"])
async def get_comments(request: Request):
    """
    GET endpoint to answer a question"""
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        agent = CommentAgent()
        comments = await agent(list_of_posts=parse_obj_as(List[Post], request.json))
        return json({"success": True, "comments": [c.dict() for c in comments]})
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})
    finally:
        logging.debug(
            "End of answer_question_get request, total time %.3f",
            (time.perf_counter() - start_counter),
        )


class ProxiedDocAgent:
    """
    Wrapper for all Doc and Cache logic
    """

    async def process_file_and_refresh_cache(
        self, sanic_app: Sanic, request: Request
    ) -> JSONResponse:
        """
        process file then refresh the cache
        """
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

                logging.info("adding files to customer service %s\n", "\n".join(paths))
                await add_files_to_customer_service(paths, flush_index=True)
            sanic_app.add_task(warmup_task())
            return json({"success": True})
        except Exception as e:
            logging.exception(e)
            return json({"success": False, "error": str(e)})

    async def refresh_cache(self, sanic_app: Sanic, request: Request) -> JSONResponse:
        """
        Trigger a refresh cache task
        """
        # pylint: disable=broad-except
        try:
            sanic_app.add_task(warmup_task())
            return json({"success": True})
        except Exception as e:
            logging.exception(e)
            return json({"success": False, "error": str(e)})


class ProxiedQAAgent:
    """
    Proxy agent for the QA logic
    """

    def __init__(self, agent: AbstractAgent) -> None:
        self.agent = agent

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
        cache = RedisCacheStoreStrategy.get_instance()
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

    async def answer_question(
        self, question: str, streaming: bool = False, callbacks=None
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
            ans, stats = await self.agent.answer_question(
                question=question, streaming=streaming, callbacks=callbacks
            )
            return self._create_result(ans, stats, False)
        else:
            return await self._answer_question_with_cache(
                question=question, streaming=streaming, callbacks=callbacks
            )


async def setup_resources(sanic_app: Sanic):
    from kbgpt.lib.db.mysql import Crud

    crud = Crud(profile.db_url)
    crud.create_tables()


app.register_listener(setup_resources, "before_server_start")


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

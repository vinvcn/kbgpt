"""
qa api
"""
import logging
import time
from json import dumps

from sanic import Blueprint, Request
from sanic.response import json

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.svc.aigc.qa.cache_qa_services import ProxiedQAAgent
from kbgpt.svc.aigc.qa.file_services import ProxiedDocAgent
from kbgpt.svc.aigc.qa.qa_services import QAagent

QA = Blueprint("qa", url_prefix="qa")


@QA.route("/get_qa", methods=["GET", "POST"])
async def answer_question_get(request: Request):
    """
    GET endpoint to answer a question"""
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        question = request.json["question"]
        logging.info("handling request: \n%s", dumps(request.json, indent=4))
        agent = ProxiedQAAgent(request.app, QAagent.get_instance())
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
@QA.route("/stream_qa", methods=["GET", "POST"])
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
        agent = ProxiedQAAgent(request.app, QAagent.get_instance())
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


@QA.route("/warmup_cache", methods=["GET", "POST"])
async def warmup_cache(request: Request):
    """
    trigger warm up task without updating documents
    """
    agent = ProxiedDocAgent()
    return await agent.refresh_cache(sanic_app=request.app, request=request)


@QA.route("/doc_version", methods=["GET"])
async def doc_version(request: Request):  # pylint: disable=unused-argument
    """
    get the doc version and timestamp
    """
    cache: RedisCacheStoreStrategy = request.app.ctx.redicache
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


@QA.route("/process_file", methods=["POST"])
async def process_file(request: Request):
    """
    POST endpoint to process file"""
    # pylint: disable=broad-except
    agent = ProxiedDocAgent()
    return await agent.process_file_and_refresh_cache(
        sanic_app=request.app, request=request
    )

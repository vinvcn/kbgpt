"""
qa api
"""
import asyncio
import logging
import time
from json import dumps

from sanic import Blueprint, Request, text
from sanic_ext import openapi, validate

from kbgpt.api.aigc.agg import (
    bouncing_ask,
    get_recommendation,
    get_recommendation_by_name,
    score,
)
from kbgpt.api.aigc.qa_models import DocInfo, GetRecomm, QAResponse, Question
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse, OpenAIResponseBase
from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.svc.aigc.qa.cache_qa_services import ProxiedQAAgent
from kbgpt.svc.aigc.qa.file_services import ProxiedDocAgent
from kbgpt.svc.aigc.qa.qa_services import QAagent

QA = Blueprint("qa", url_prefix="qa")


@QA.route("/get_qa", methods=["GET"])
@openapi.description(
    "Get answer for the given question based on "
    + "similarity matching with the knowledge base"
)
@openapi.definition(body={API_CONTENT_TYPE: Question.schema()})
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: QAResponse.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=Question)
async def answer_question_get(request: Request, body: Question):
    """
    Get answer for the given question
    """
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        question = body.question
        logging.info("handling request: \n%s", dumps(body.dict(), indent=4))
        agent = ProxiedQAAgent(request.app, QAagent.get_instance())
        result: QAResponse = await agent.answer_question(question=question)
        return jtext(result)
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(success=False, error=str(e)))
    finally:
        logging.debug(
            "End of answer_question_get request, total time %.3f",
            (time.perf_counter() - start_counter),
        )


@QA.route("/get_recomm", methods=["POST"])
@openapi.description("get recomendation for given products")
@openapi.definition(body={API_CONTENT_TYPE: GetRecomm.schema()})
@validate(json=GetRecomm)
async def get_recomm(request: Request, body: GetRecomm):
    try:
        if body.product_name:
            result = await get_recommendation_by_name(body.product_name)
        else:
            result = await get_recommendation(body.product_id)
        return text(result.json(exclude_none=True), content_type=API_CONTENT_TYPE)
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(success=False, error=str(e)))


# pylint: disable=unused-argument
@QA.route("/stream_qa", methods=["GET", "POST"])
@openapi.description(
    "In streaming, get answer for the given question based on "
    + "similarity matching with the knowledge base"
)
@openapi.definition(body={API_CONTENT_TYPE: Question.schema()})
@validate(json=Question)
async def answer_question(request: Request, body: Question):
    """
    Streaming endpoint to answer a question
    """
    headers = {"Cache-Control": "no-cache"}
    response = await request.respond(
        headers=headers, content_type="text/event-stream; charset=utf-8"
    )
    callbacks = [StreamingAsyncHandler(response.send)]
    start_counter = time.perf_counter()
    # pylint: disable=broad-except
    try:
        question = body.question
        logging.info("handling request: \n%s", dumps(body.dict(), indent=4))
        agent = ProxiedQAAgent(request.app, QAagent.get_instance())
        intent = await score(question, 80)
        if intent and len(intent.matching) >= 2:
            result = await bouncing_ask(intent.matching, question, callbacks[0])
        else:
            result = await agent.answer_question(
                question=question, streaming=True, callbacks=callbacks
            )
        if intent:
            result.intents = intent.matching
        await response.send(f"data: {result.json(exclude_none=True)}")
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
@openapi.description(
    "Warm up cached questions according to the latest documents" + " in knowledge base"
)
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: OpenAIResponseBase.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
async def warmup_cache(request: Request):
    """
    trigger warm up task without updating documents
    """
    agent = ProxiedDocAgent()
    return await agent.refresh_cache(sanic_app=request.app, request=request)


@QA.route("/doc_version", methods=["GET"])
@openapi.description("Get the information about the document in knowledge base.")
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: DocInfo.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
async def doc_version(request: Request):  # pylint: disable=unused-argument
    """
    get the doc version and timestamp
    """
    cache: RedisCacheStoreStrategy = request.app.ctx.redicache
    # pylint: disable=broad-except
    try:
        index_version = cache.get_index_version()
        return jtext(
            DocInfo(
                success=True,
                version=index_version.uuid,
                timestamp=index_version.timestamp,
            )
        )
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(success=False, error=str(e)))


@QA.route("/process_file", methods=["POST"])
@openapi.description("Upload file as the new knowledge base.")
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: OpenAIResponseBase.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
async def process_file(request: Request):
    """
    POST endpoint to process file"""
    # pylint: disable=broad-except
    agent = ProxiedDocAgent()
    return await agent.process_file_and_refresh_cache(
        sanic_app=request.app, request=request
    )

"""
define the Sanic app
"""
import logging
import time
from json import dumps
from typing import List

from pydantic import parse_obj_as
from sanic import Request, Sanic
from sanic.response import json
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.svc.cached_qa_agent import ProxiedQAAgent
from kbgpt.svc.comment_service import CommentAgent
from kbgpt.svc.file_services import ProxiedDocAgent
from kbgpt.svc.models.comment import Post
from kbgpt.svc.qa_services import QAagent
from kbgpt.web.callbacks import StreamingAsyncHandler
from kbgpt.web.globals import app
from kbgpt.web.resources import ResourceMgr


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
    cache:RedisCacheStoreStrategy = app.ctx.redicache
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
        agent = ProxiedQAAgent(app, QAagent.get_instance())
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
        agent = ProxiedQAAgent(app, QAagent.get_instance())
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
        agent = CommentAgent(request.app)
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


@app.before_server_start
async def setup_resources(sanic_app: Sanic, loop):
    """
    Setup all resources to be used later on.
    """

    crud = Crud(profile.db_url)
    sql_emitter = MySqlEmitter(crud)
    mgr = ResourceMgr(sanic_app)
    mgr.add(crud)
    mgr.add(sql_emitter)

    await mgr.init_all()
    sanic_app.ctx.res = mgr

    sanic_app.ctx.redicache = RedisCacheStoreStrategy()
    sanic_app.add_task(sql_emitter.aloop_drain(), name="sql_emitter_drain_loop")


@app.after_server_stop
async def cleanup_resources(sanic_app: Sanic):
    """
    Clean up resources setup earlier.
    """
    mgr: ResourceMgr = sanic_app.ctx.res
    await mgr.destroy_all()


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

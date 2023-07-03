"""
comment apis
"""
import logging
import time
from typing import List

from pydantic import parse_obj_as
from sanic import Blueprint, Request
from sanic.response import json

from kbgpt.svc.aigc.comment.models import Post
from kbgpt.svc.aigc.comment.services import CommentAgent

COMMENT = Blueprint("comment", url_prefix="comment")


@COMMENT.route("/get_comments", methods=["GET", "POST"])
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

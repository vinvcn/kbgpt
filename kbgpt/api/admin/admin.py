import logging

from sanic import Blueprint, Request
from sanic_ext import openapi, validate

from kbgpt.api.admin.models import TaskStatusRequest, TaskStatusResponse
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.tasks.manager import TaskManager

TASK = Blueprint("task", url_prefix="task")


@TASK.route("/status", methods=["GET"])
@openapi.description("get the report")
@openapi.definition(body={API_CONTENT_TYPE: TaskStatusRequest})
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: TaskStatusResponse.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=TaskStatusRequest)
async def get_task_status(request: Request, body: TaskStatusRequest):
    """
    GET endpoint to answer a question"""
    # pylint: disable=broad-except
    try:
        mgr: TaskManager = request.app.ctx.res.get(TaskManager.__name__)
        record = await mgr.get_task(body.task_name, body.task_id)
        resp = TaskStatusResponse.from_orm(record)
        return jtext(resp)
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(repr(e)))

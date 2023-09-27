import logging
import traceback
from typing import Type

from pydantic import BaseModel
from sanic import Sanic
from sanic.response import text

from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse
from kbgpt.svc.aigc import Agent


def jtext(model: BaseModel):
    return text(model.json(), content_type=API_CONTENT_TYPE)


async def invoke_agent(app: Sanic, agent_cls: Type[Agent], body: BaseModel):
    try:
        agent = agent_cls(app=app)
        result = await agent.analyze(body)
        return jtext(result)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.exception(e)
        error_msg = "".join(traceback.format_exception(e))
        return jtext(ErrorResponse(success=False, error=error_msg))

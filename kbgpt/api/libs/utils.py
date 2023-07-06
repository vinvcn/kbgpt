
from pydantic import BaseModel
from sanic.response import text

from kbgpt.api.constants import API_CONTENT_TYPE


def jtext(model:BaseModel):
    return text(model.json(), content_type=API_CONTENT_TYPE)

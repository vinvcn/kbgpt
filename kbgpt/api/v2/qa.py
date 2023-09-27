"""
qa api
"""
import logging
import time
from json import dumps

from sanic import Blueprint, Request, text
from sanic_ext import openapi, validate

from config import profile
from kbgpt.api.aigc.agg import (
    bouncing_ask,
    get_recommendation,
    get_recommendation_by_conversation,
    get_recommendation_by_name,
)
from kbgpt.api.aigc.agg_models import IntentResp, Matching
from kbgpt.api.aigc.qa_models import (
    DocInfo,
    GetRecomm,
    QAResponse,
    Question,
    RecommType,
)
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse, OpenAIResponseBase
from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.vector_store import BusinessType, create_vector_store_strategy
from kbgpt.svc.aigc.qa.cache_qa_services import ProxiedQAAgent
from kbgpt.svc.aigc.qa.file_services import ProxiedDocAgent
from kbgpt.svc.aigc.qa.qa_services import QAagent

QA = Blueprint("qa", url_prefix="qa")


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

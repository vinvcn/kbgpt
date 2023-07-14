"""
comment apis
"""


from sanic import Blueprint, Request
from sanic_ext import openapi, validate

from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse
from kbgpt.api.libs.utils import invoke_agent
from kbgpt.api.senti.models import Sentiment, SentimentResponse
from kbgpt.svc.aigc.sentiment import SentimentAgent

SENTIMENT = Blueprint("sentiment", url_prefix="senti")


@SENTIMENT.route("get_sentiment", ["GET"])
@openapi.description("Get the sentiment for the given content")
@openapi.definition(body={API_CONTENT_TYPE: Sentiment.schema()})
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: SentimentResponse.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=Sentiment)
async def get_sentiment(request: Request, body: Sentiment):
    """Get the sentiment for the given content"""
    return await invoke_agent(request.app, SentimentAgent, body)

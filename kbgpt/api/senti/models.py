

from pydantic import BaseModel, Field

from kbgpt.api.libs.base_model import ResponseBase


class SentimentResponse(ResponseBase):
    """ sentiment response """

    level: int
    description: str


class Sentiment(BaseModel):
    """ sentiment model """
    content: str
    rating: int

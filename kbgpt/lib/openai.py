"""
OpenAI clients
"""
__all__ = ["openai_embeddings", "chat_open_ai_llm"]
from typing import List

from langchain.callbacks import AsyncCallbackManager
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from openai import Embedding

from config import profile


# pylint: disable=abstract-method
class HackedEmbedding(Embedding):
    """
    add timeout and retry to the create method
    """

    @classmethod
    def create(cls, *args, **kwargs):
        return super().create(
            request_timeout=profile.qa.request_timeout, *args, **kwargs
        )

    @classmethod
    async def acreate(cls, *args, **kwargs):
        return await super().acreate(
            request_timeout=profile.qa.request_timeout, *args, **kwargs
        )


openai_embeddings = OpenAIEmbeddings(max_retries=profile.qa.request_retry)
openai_embeddings.client = HackedEmbedding


def chat_open_ai_llm(
    streaming: bool = False, handlers: List[BaseCallbackHandler] = None
) -> ChatOpenAI:
    """
    Get the chat open ai llm
    """
    cbm = AsyncCallbackManager(handlers) if handlers else None
    return ChatOpenAI(
        model_name=profile.qa.generative_model,
        n=1,
        request_timeout=profile.qa.request_timeout,
        max_retries=profile.qa.request_retry,
        temperature=profile.qa.customer_service_temperature,
        max_tokens=1000,
        streaming=streaming,
        callback_manager=cbm,
    )

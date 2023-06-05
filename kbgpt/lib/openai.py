"""
OpenAI clients
"""
__all__ = ["openai_embeddings", "chat_open_ai_llm"]
from typing import List

from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from config import profile

openai_embeddings = OpenAIEmbeddings(
    max_retries=profile.qa.request_retry,
    request_timeout=profile.qa.request_timeout,
)


def chat_open_ai_llm(
    streaming: bool = False, handlers: List[BaseCallbackHandler] = None
) -> ChatOpenAI:
    """
    Get the chat open ai llm
    """
    return ChatOpenAI(
        model_name=profile.qa.generative_model,
        n=1,
        request_timeout=profile.qa.request_timeout,
        max_retries=profile.qa.request_retry,
        temperature=profile.qa.customer_service_temperature,
        max_tokens=1000,
        streaming=streaming,
        callbacks=handlers,
    )

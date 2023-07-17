"""
open ai callbacks
"""
import logging
from typing import Any, Callable

from langchain.callbacks.base import AsyncCallbackHandler
from pydantic import BaseModel


class Token(BaseModel):
    """ OpenAI token """
    token: str

    def json(self, *args, **kwargs) -> str:
        json_str = super().json(*args, ensure_ascii=False, **kwargs)
        result = json_str.replace("\\n","<br/>")
        return result


# pylint: disable = abstract-method
class StreamingAsyncHandler(AsyncCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""

    def __init__(self, send: Callable):
        self.send = send

    async def on_llm_new_token(
        self,
        token: str,
        **kwargs: Any,
    ) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        await self.send(f"data: {Token(token=token).json()}\n")

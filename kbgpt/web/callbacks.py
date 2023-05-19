from typing import Any

from langchain.callbacks.base import AsyncCallbackHandler
from sanic.server.websockets.impl import WebsocketImplProtocol


# pylint: disable = abstract-method
class StreamingAsyncHandler(AsyncCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""

    def __init__(self, ws: WebsocketImplProtocol):
        self.ws = ws

    async def on_llm_new_token(
        self,
        token: str,
        **kwargs: Any,
    ) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        await self.ws.send(token)

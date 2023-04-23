import asyncio
from typing import Any, Dict, List, Optional, Union

from langchain.callbacks import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from sanic.server.websockets.impl import WebsocketImplProtocol


class StreamingTextCallbackHandler(BaseCallbackHandler):
    """Streaming Text Callback Handler."""

    def __init__(self, websocket: WebsocketImplProtocol):
        self.websocket = websocket

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        asyncio.run(self.websocket.send(token))

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when LLM errors."""

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when chain errors."""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when tool errors."""

    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""


# class StreamingLLMCallbackHandler(AsyncCallbackHandler):
#     """Callback handler for streaming LLM responses."""

#     def __init__(self, websocket):
#         self.websocket = websocket

#     async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
#         resp = ChatResponse(sender="bot", message=token, type="stream")
#         await self.websocket.send_json(resp.dict())


# class QuestionGenCallbackHandler(AsyncCallbackHandler):
#     """Callback handler for question generation."""

#     def __init__(self, websocket):
#         self.websocket = websocket

#     async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
#         """Run when LLM starts running."""
#         resp = ChatResponse(sender="bot", message="Synthesizing question...", type="info")
#         await self.websocket.send_json(resp.dict())

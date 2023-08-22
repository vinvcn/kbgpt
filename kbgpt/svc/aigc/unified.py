from pydantic import BaseModel
from sanic import Request

from kbgpt.api.aigc.qa_models import Question
from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor

from .qa.qa_graph import QA_GRAPH


class AIGCAgent:
    def __init__(self, request: Request):
        self.request = request

    async def invoke(self, body: Question):
        headers = {"Cache-Control": "no-cache"}
        response = await self.request.respond(
            headers=headers, content_type="text/event-stream; charset=utf-8"
        )
        callbacks = [StreamingAsyncHandler(response.send)]
        await GraphExecutor(QA_GRAPH).exec(
            {
                "question": body.question,
                "words_limit": 38,
                "callbacks": callbacks,
            }
        )

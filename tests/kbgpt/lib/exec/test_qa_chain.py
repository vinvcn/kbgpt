from collections import OrderedDict

import pytest

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.api.v2.defs.qa import qa_graph
from kbgpt.lib.exec.engines.embed import Embed
from kbgpt.lib.exec.engines.similarity_search import SimilaritySearch
from kbgpt.lib.exec.engines.simple_engine import SimpleEngine
from kbgpt.lib.exec.pipeline.checker_models import EqCheckerMod
from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor


@pytest.fixture
def graph():
    return qa_graph()


async def aprint(*args, **kwargs):
    print(*args, **kwargs)


@pytest.mark.asyncio
async def test_qa_chain(graph):
    result = await GraphExecutor(graph).exec(
        {
            "question": "Smart Nivesh",
            "words_limit": 38,
            "callbacks": [StreamingAsyncHandler(aprint)],
        }
    )
    assert "answer" in result and "bullsmart" in result["answer"].lower()


@pytest.mark.asyncio
async def test_qa_chain_(graph):
    result = await GraphExecutor(graph).exec(
        {
            "question": "nihao",
            "words_limit": 38,
            "callbacks": [StreamingAsyncHandler(aprint)],
        }
    )
    assert len(result.keys()) == 1 and "answer" in result

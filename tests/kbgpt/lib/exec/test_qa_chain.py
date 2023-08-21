from collections import OrderedDict

import pytest

from kbgpt.api.v2.defs.qa import qa_graph
from kbgpt.lib.exec.engines import Embed, SimilaritySearch, SimpleEngine
from kbgpt.lib.exec.exec import GraphExecutor
from kbgpt.lib.exec.models import EqCheckerMod


@pytest.fixture
def graph():
    return qa_graph


@pytest.mark.asyncio
async def test_qa_chain(graph):
    result = await GraphExecutor(graph).exec(
        {"question": "Smart Nivesh", "words_limit": 38}
    )
    assert "answer" in result and "bullsmart" in result["answer"].lower()


@pytest.mark.asyncio
async def test_qa_chain_(graph):
    result = await GraphExecutor(graph).exec({"question": "redeem", "words_limit": 38})

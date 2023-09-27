import pytest

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor
from kbgpt.svc.aigc.qa.qa_graph import qa_graph


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


# @pytest.mark.asyncio
# async def test_qa_chain_(graph):
#     result = await GraphExecutor(graph).exec(
#         {
#             "question": "nihao",
#             "words_limit": 38,
#             "callbacks": [StreamingAsyncHandler(aprint)],
#         }
#     )
#     assert len(result.keys()) == 1 and "answer" in result

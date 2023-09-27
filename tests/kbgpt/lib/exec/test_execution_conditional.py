import pytest

from kbgpt.lib.exec.engines.configs.models import TestMod
from kbgpt.lib.exec.pipeline.checker_models import EqCheckerMod
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)


@pytest.fixture
def conditional_nodes():
    A = GraphNode(
        node=Node(
            id="A",
            engine=TestMod(input_keys=["content"], output={"answer": "no"}),
            frm=SelectorMultiplexer(
                selectors=[Selector(node=K_SEED, key="question", to_key="content")]
            ),
            sel={"answer": "content"},
        ),
        src=[],
    )
    B = GraphNode(
        node=Node(
            id="B",
            engine=TestMod(input_keys=["content"], output={"answer": "B"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="A", key="content")]),
            sel={"answer": "content"},
            pre=EqCheckerMod(key="content", trg_value="yes"),
        ),
        src=[A],
    )
    C = GraphNode(
        node=Node(
            id="C",
            engine=TestMod(input_keys=["content"], output={"answer": "C"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="A", key="content")]),
            sel={"answer": "content"},
            pre=EqCheckerMod(key="content", trg_value="no"),
        ),
        src=[A],
    )
    return [A, B, C]


@pytest.mark.asyncio
async def test_conditional_execution(conditional_nodes):
    graph = Graph(
        nodes=conditional_nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="C", key="content"),
                Selector(node="B", key="content"),
            ],
            mode=MultiplexerType.ANY,
        ),
    )

    result = await GraphExecutor(graph).exec({"question": "some"})
    assert result["content"] == "C", "answer should be equal to C"


@pytest.mark.asyncio
async def test_conditional_execution_except(conditional_nodes):
    graph = Graph(
        nodes=conditional_nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="C", key="content"),
                Selector(node="B", key="content"),
            ],
            mode=MultiplexerType.ALL,
        ),
    )

    try:
        await GraphExecutor(graph).exec({"question": "some"})
        assert False, "shound't reach here"
    except AssertionError as e:
        assert "multiplexer type is MultiplexerType.ALL" in str(e)


# @pytest.mark.asyncio
# async def test_conditional_multiplexer_first(conditional_nodes):
#     graph = Graph(
#         nodes=conditional_nodes,
#         sel=SelectorMultiplexer(
#             selectors=[
#                 Selector(node="C", key="content", to_key="ccontent"),
#                 Selector(node="A", key="content", to_key="acontent"),
#             ],
#             mode=MultiplexerType.FIRST,
#         ),
#     )

#     result = await GraphExecutor(graph).exec({"question": "some"})
#     assert (
#         "ccontent" in result and result["ccontent"] == "C" and "acontent" not in result
#     )

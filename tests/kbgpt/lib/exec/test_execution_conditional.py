import pytest

from kbgpt.lib.exec.exec import GraphExecutor
from kbgpt.lib.exec.models import *


@pytest.fixture
def conditional_nodes():
    A = GraphNode(
        node=Node(
            id="A",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "no"}),
            frm=SelectorMultiplexer(
                selectors=[Selector(node="seed", key="question", to_key="content")]
            ),
            sel={"answer": "content"},
        ),
        src=[],
    )
    B = GraphNode(
        node=Node(
            id="B",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "B"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="A", key="content")]),
            sel={"answer": "content"},
            pre=EqCheckerMod(key="content", trg_value="yes"),
        ),
        src=[A],
    )
    C = GraphNode(
        node=Node(
            id="C",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "C"}),
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
            mode=MultiplexerType.SOME,
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


@pytest.mark.asyncio
async def test_conditional_multiplexer_first(conditional_nodes):
    graph = Graph(
        nodes=conditional_nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="C", key="content", to_key="ccontent"),
                Selector(node="A", key="content", to_key="acontent"),
            ],
            mode=MultiplexerType.FIRST,
        ),
    )

    result = await GraphExecutor(graph).exec({"question": "some"})
    assert (
        "ccontent" in result and result["ccontent"] == "C" and "acontent" not in result
    )

import json
import logging

import pytest

from kbgpt.lib.exec.engines import TestEngine
from kbgpt.lib.exec.exec import GraphExecutor
from kbgpt.lib.exec.models import *


@pytest.fixture
def linear_graph():
    node1 = GraphNode(
        node=Node(
            engine=TestEngineMod(
                input_keys=["question"], output={"answer1": "yes", "answer2": "No"}
            ),
            id="test1",
            frm=SelectorMultiplexer(selectors=[Selector(node="seed", key="question")]),
        )
    )

    node2 = GraphNode(
        node=Node(
            engine=TestEngineMod(input_keys=["content"], output={"uri": "http://asdf"}),
            id="test2",
            frm=SelectorMultiplexer(
                selectors=[Selector(node="test1", key="answer1", to_key="content")]
            ),
        ),
        src=[node1],
    )

    node3 = GraphNode(
        node=Node(
            engine=TestEngineMod(input_keys=["content"], output={"answer": "Yes"}),
            id="test3",
            frm=SelectorMultiplexer(
                selectors=[Selector(node="test2", key="uri", to_key="content")],
            ),
        ),
        src=[node2],
    )

    graph = Graph(
        nodes=[node1, node2, node3],
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="test1", key="answer1", to_key="secondary"),
                Selector(node="test3", key="answer"),
            ]
        ),
    )
    yield graph


@pytest.mark.asyncio
async def test_engine_execution(linear_graph):
    """test a linear execution"""

    result = await GraphExecutor(linear_graph).exec({"question": "how are you?"})
    # logging.info(json.dumps(result, indent=4))
    assert result["secondary"] == "yes", result["answer"] == "Yes"


@pytest.mark.asyncio
async def test_diverge_execution():
    A = GraphNode(
        node=Node(
            id="A",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "A"}),
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
        ),
        src=[A],
    )
    C = GraphNode(
        node=Node(
            id="C",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "C"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="A", key="content")]),
            sel={"answer": "content"},
        ),
        src=[A],
    )
    D = GraphNode(
        node=Node(
            id="D",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "D"}),
            sel={"answer": "content"},
            frm=SelectorMultiplexer(selectors=[Selector(node="B", key="content")]),
        ),
        src=[A, B],
    )
    E = GraphNode(
        node=Node(
            id="E",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "E"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="C", key="content")]),
            sel={"answer": "content"},
        ),
        src=[C, D],
    )
    F = GraphNode(
        node=Node(
            id="F",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "F"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="E", key="content")]),
            sel={"answer": "content"},
        ),
        src=[E],
    )
    G = GraphNode(
        node=Node(
            id="G",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "G"}),
            frm=SelectorMultiplexer(selectors=[Selector(node="D", key="content")]),
            sel={"answer": "content"},
        ),
        src=[D],
    )

    # Creating a graph with the above nodes
    graph = Graph(
        nodes=[A, B, C, D, E, F, G],
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="F", key="content", to_key="Foutput"),
                Selector(node="G", key="content", to_key="Goutput"),
            ]
        ),
    )

    result = await GraphExecutor(graph).exec({"question": "how are you?"})
    logging.info(json.dumps(result, indent=4))
    assert result["Foutput"] == "F", result["Goutput"] == "G"


@pytest.mark.asyncio
async def test_some_multiplexer_execution(linear_graph):
    """test a linear execution"""

    linear_graph.sel = SelectorMultiplexer(
        selectors=[
            Selector(node="test1", key="answer1", to_key="secondary"),
            Selector(node="none_exists", key="answer", to_key="none"),
        ],
        mode=MultiplexerType.SOME,
    )

    result = await GraphExecutor(linear_graph).exec({"question": "how are you?"})
    # logging.info(json.dumps(result, indent=4))
    assert result["secondary"] == "yes" and "answer" not in result


@pytest.mark.asyncio
async def test_pre_cond_failed_executioin(linear_graph: Graph):
    node: GraphNode = linear_graph.nodes[2]
    node.node.pre = EqCheckerMod(key="uri", trg_value="not equal value")
    linear_graph.sel = SelectorMultiplexer(
        selectors=[
            Selector(node="test1", key="answer1", to_key="secondary"),
            Selector(node="test3", key="answer"),
        ],
        mode=MultiplexerType.SOME,
    )
    result = await GraphExecutor(linear_graph).exec({"question": "how are you?"})
    assert result["secondary"] == "yes" and "answer" not in result


# test

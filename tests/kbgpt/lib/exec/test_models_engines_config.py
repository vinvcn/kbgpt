import json
import logging

import pytest

from kbgpt.lib.exec.engines import TestEngine
from kbgpt.lib.exec.exec import GraphExecutor
from kbgpt.lib.exec.models import *


@pytest.mark.asyncio
async def test_engine_execution():
    """test a linear execution"""
    node1 = GraphNode(
        node=Node(
            engine=TestEngineMod(
                input_keys=["question"], output={"answer1": "yes", "answer2": "No"}
            ),
            id="test1",
            frm=[Selector(node="seed", key="question")],
        )
    )

    node2 = GraphNode(
        node=Node(
            engine=TestEngineMod(input_keys=["content"], output={"uri": "http://asdf"}),
            id="test2",
            frm=[Selector(node="test1", key="answer1", to_key="content")],
        ),
        src=[node1],
    )

    node3 = GraphNode(
        node=Node(
            engine=TestEngineMod(input_keys=["content"], output={"answer": "Yes"}),
            id="test3",
            frm=[Selector(node="test2", key="uri", to_key="content")],
        ),
        src=[node2],
    )

    graph = Graph(
        nodes=[node1, node2, node3],
        sel=[
            Selector(node="test1", key="answer1", to_key="secondary"),
            Selector(node="test3", key="answer"),
        ],
    )

    result = await GraphExecutor(graph).exec({"question": "how are you?"})
    # logging.info(json.dumps(result, indent=4))
    assert result["secondary"] == "yes", result["answer"] == "Yes"


@pytest.mark.asyncio
async def test_diverge_execution():
    A = GraphNode(
        node=Node(
            id="A",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "A"}),
            frm=Selector(node="seed", key="question", to_key="content"),
            sel={"answer": "content"},
        ),
        src=[],
    )
    B = GraphNode(
        node=Node(
            id="B",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "B"}),
            frm=Selector(node="A", key="content"),
            sel={"answer": "content"},
        ),
        src=[A],
    )
    C = GraphNode(
        node=Node(
            id="C",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "C"}),
            frm=Selector(node="A", key="content"),
            sel={"answer": "content"},
        ),
        src=[A],
    )
    D = GraphNode(
        node=Node(
            id="D",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "D"}),
            sel={"answer": "content"},
            frm=Selector(node="B", key="content"),
        ),
        src=[A, B],
    )
    E = GraphNode(
        node=Node(
            id="E",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "E"}),
            frm=Selector(node="C", key="content"),
            sel={"answer": "content"},
        ),
        src=[C, D],
    )
    F = GraphNode(
        node=Node(
            id="F",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "F"}),
            frm=Selector(node="E", key="content"),
            sel={"answer": "content"},
        ),
        src=[E],
    )
    G = GraphNode(
        node=Node(
            id="G",
            engine=TestEngineMod(input_keys=["content"], output={"answer": "G"}),
            frm=Selector(node="D", key="content"),
            sel={"answer": "content"},
        ),
        src=[D],
    )

    # Creating a graph with the above nodes
    graph = Graph(
        nodes=[A, B, C, D, E, F, G],
        sel=[
            Selector(node="F", key="content", to_key="Foutput"),
            Selector(node="G", key="content", to_key="Goutput"),
        ],
    )

    result = await GraphExecutor(graph).exec({"question": "how are you?"})
    logging.info(json.dumps(result, indent=4))
    assert result["Foutput"] == "F", result["Goutput"] == "G"


# def test_engine_creation_1():
#     # pylint: disable = unhashable-member
#     report = GraphNode(
#         node=Node(
#             engine=ReportEngineMod(
#                 name="report.daily.jinja",
#                 render_config={
#                     "coverBreakSec": 1.7,
#                     "pageBreakSec": 1,
#                     "listingBreakSec": 1,
#                 },
#             ),
#             id="report_daily",
#             frm={
#                 Addresser(node="seed", key="**"): "**",
#             },
#         ),
#         src=[],
#     )

#     adjust = GraphNode(
#         node=Node(
#             engine=SimpleEngineMod(name="report.daily.adjust"),
#             id="adjust_engine",
#             frm={
#                 Addresser(node="report_daily", key="content"): "content",
#             },
#         ),
#         src=[report],
#     )
#     polish = GraphNode(
#         node=Node(
#             engine=SimpleEngineMod(name="report.daily.polish"),
#             id="polish_engine",
#             frm={
#                 Addresser(node="adjust_engine", key="content"): "content",
#             },
#         ),
#         src=[adjust],
#     )

#     graph = Graph(nodes=[report, adjust, polish])

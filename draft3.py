import asyncio
from datetime import date, timedelta
from textwrap import indent

from redis import Redis

from config import profile
from kbgpt.api.aigc.report_models import Report, Type
from kbgpt.lib.exec.models import *
from kbgpt.lib.templates.rendering.models import RedisTemplateProvider, TemplateRepo

# pylint: disable = unhashable-member
report = GraphNode(
    node=Node(
        engine=ReportEngineMod(
            name="report.daily.jinja",
            render_config={
                "coverBreakSec": 1.7,
                "pageBreakSec": 1,
                "listingBreakSec": 1,
            },
        ),
        id="report_daily",
        frm={
            SelectorMod(node="seed", key="**"): "**",
        },
    )
)

adjust = GraphNode(
    node=Node(
        engine=SimpleEngineMod(name="report.daily.adjust"),
        id="adjust_engine",
        frm={
            SelectorMod(node="report_daily", key="content"): "content",
        },
    ),
)
polish = GraphNode(
    node=Node(
        engine=SimpleEngineMod(name="report.daily.polish"),
        id="polish_engine",
        frm={
            SelectorMod(node="adjust_engine", key="content"): "content",
        },
    ),
)


# # Example usage
# node1 = GraphNode(name="Task 1")
# node2 = GraphNode(name="Task 2")
# node3 = GraphNode(name="Task 3")
# node4 = GraphNode(name="Task 4")

# node2.src = [node1]
# node3.src = [node1, node2]
# node4.src = [node3]

# for iteration, node_list in enumerate(GraphNode.topological_sort(node1), start=1):
#     print(f"Iteration {iteration}: {[node for node in node_list]}")
# Creating sample nodes
A = GraphNode(node=Node(id="A"), src=[])
B = GraphNode(node=Node(id="B"), src=[A])
C = GraphNode(node=Node(id="C"), src=[A])
D = GraphNode(node=Node(id="D"), src=[A, B])
E = GraphNode(node=Node(id="E"), src=[C, D])
F = GraphNode(node=Node(id="F"), src=[E])
G = GraphNode(node=Node(id="G"), src=[D])

# Creating a graph with the above nodes
graph = Graph(nodes=[A, B, C, D, E, F, G])

# Checking if the graph is a DAG
print(graph.is_dag(G))  # Output: True

# Getting nodes with 0 source nodes using get_next_nodes method
# next_nodes = graph.get_next_nodes(A)
# for node in next_nodes:
#     print(node.node.id)  # Output: B, C

# Getting nodes with 0 source nodes using iter_next_nodes method
for ls_nodes in graph.iter_next_nodes():
    print(ls_nodes)

# After calling iter_next_nodes, other source nodes should be removed from the original graph
# for node in graph.nodes:
#     print(node.src)  # Output: [], [A], [A], [A], [C], [E], []

import pytest

from kbgpt.lib.exec.models import *


def test_is_connected_empty_graph():
    # Create an instance of Graph with no nodes
    graph = Graph(nodes=None, sel=SelectorMultiplexer(selectors=[]))

    # Call the is_connected method and assert that it returns True
    assert graph.is_connected() is True


def test_is_connected_true_1():
    # Create an instance of Graph with connected nodes
    node1 = GraphNode(node=Node(id="1"), src=[])
    node2 = GraphNode(node=Node(id="2"), src=[node1])
    node3 = GraphNode(node=Node(id="3"), src=[node2])
    node4 = GraphNode(node=Node(id="4"), src=[node3])
    node5 = GraphNode(node=Node(id="5"), src=[node2])

    graph = Graph(
        nodes=[node1, node2, node3, node4, node5], sel=SelectorMultiplexer(selectors=[])
    )

    # Call the is_connected method and assert that it returns True
    assert graph.is_connected() is True


def test_is_connected_true():
    # Create an instance of Graph with connected nodes
    node1 = GraphNode(node=Node(id="1"), src=[])
    node2 = GraphNode(node=Node(id="2"), src=[node1])
    node3 = GraphNode(node=Node(id="3"), src=[node2])
    node4 = GraphNode(node=Node(id="4"), src=[node3])

    graph = Graph(
        nodes=[node1, node2, node3, node4], sel=SelectorMultiplexer(selectors=[])
    )

    # Call the is_connected method and assert that it returns True
    assert graph.is_connected() is True


def test_is_connected_false_1():
    # Create an instance of Graph with disconnected nodes
    node1 = GraphNode(node=Node(id="1"), src=[])
    node2 = GraphNode(node=Node(id="2"), src=[node1])
    node3 = GraphNode(node=Node(id="3"), src=[])
    node4 = GraphNode(node=Node(id="4"), src=[node3])

    graph = Graph(
        nodes=[node1, node2, node3, node4], sel=SelectorMultiplexer(selectors=[])
    )

    # Call the is_connected method and assert that it returns False
    assert graph.is_connected() is False


def test_is_connected_false_2():
    # Create an instance of Graph with disconnected nodes
    node1 = GraphNode(node=Node(id="1"), src=[])
    node3 = GraphNode(node=Node(id="3"), src=[])

    graph = Graph(nodes=[node1, node3], sel=SelectorMultiplexer(selectors=[]))

    # Call the is_connected method and assert that it returns False
    assert graph.is_connected() is False


def test_is_dag_true():
    node1 = GraphNode(node=Node(id="1"), src=[])
    node2 = GraphNode(node=Node(id="2"), src=[node1])
    node3 = GraphNode(node=Node(id="3"), src=[])
    node4 = GraphNode(node=Node(id="4"), src=[node3])

    graph = Graph(
        nodes=[node1, node2, node3, node4], sel=SelectorMultiplexer(selectors=[])
    )

    assert graph.is_dag() is True
    assert graph.is_dag() is True


def test_is_dag_false():
    node1 = GraphNode(node=Node(id="1"), src=[])
    node1.src = [node1]

    graph = Graph(nodes=[node1], sel=SelectorMultiplexer(selectors=[]))

    assert graph.is_dag() is False


def test_is_dag_false2():
    node1 = GraphNode(node=Node(id="1"), src=[])
    node2 = GraphNode(node=Node(id="2"), src=[node1])
    node3 = GraphNode(node=Node(id="3"), src=[])
    node4 = GraphNode(node=Node(id="4"), src=[node3])

    node1.src = [node2]
    node3.src = [node1]

    graph = Graph(
        nodes=[node1, node2, node3, node4], sel=SelectorMultiplexer(selectors=[])
    )

    assert graph.is_dag() is False
    assert graph.is_dag() is False
    assert graph.is_dag() is False


def test_iter_next_nodes():
    A = GraphNode(node=Node(id="A"), src=[])
    B = GraphNode(node=Node(id="B"), src=[A])
    C = GraphNode(node=Node(id="C"), src=[A])
    D = GraphNode(node=Node(id="D"), src=[A, B])
    E = GraphNode(node=Node(id="E"), src=[C, D])
    F = GraphNode(node=Node(id="F"), src=[E])
    G = GraphNode(node=Node(id="G"), src=[D])

    # Creating a graph with the above nodes
    graph = Graph(nodes=[A, B, C, D, E, F, G], sel=SelectorMultiplexer(selectors=[]))

    # Checking if the graph is a DAG
    assert graph.is_connected() is True

    # Getting nodes with 0 source nodes using iter_next_nodes method
    for ls_nodes, ln in zip(graph.iter_next_nodes(), [1, 2, 1, 2, 1]):
        assert len(ls_nodes) == ln


def test_iter_next_nodes_encounter_dag():
    A = GraphNode(node=Node(id="A"), src=[])
    B = GraphNode(node=Node(id="B"), src=[A])
    C = GraphNode(node=Node(id="C"), src=[A])
    D = GraphNode(node=Node(id="D"), src=[A, B])
    E = GraphNode(node=Node(id="E"), src=[C, D])
    F = GraphNode(node=Node(id="F"), src=[E])
    G = GraphNode(node=Node(id="G"), src=[D])

    B.src.append(G)

    # Creating a graph with the above nodes
    graph = Graph(nodes=[A, B, C, D, E, F, G], sel=SelectorMultiplexer(selectors=[]))

    # Checking if the graph is a DAG
    assert graph.is_connected() is True

    # Getting nodes with 0 source nodes using iter_next_nodes method
    try:
        for _ in graph.iter_next_nodes():
            pass
    except AssertionError as e:
        assert str(e).startswith("Not a DAG, the graph contains a circle.")

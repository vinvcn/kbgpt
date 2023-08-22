from copy import deepcopy
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import SelectorMultiplexer


class GraphNode(BaseModel):
    node: Optional[Node]
    src: List["GraphNode"] = Field([])

    @property
    def id(self):
        return self.node.id

    def __hash__(self):
        # Customizing the hash function to use the object ID as the unique identifier
        return hash(self.node.id)

    def __eq__(self, other):
        if isinstance(other, GraphNode):
            return hash(self) == hash(other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f"GraphNode[node:{repr(self.node)}, src:{repr(self.src)}]"


class Graph(BaseModel):
    """graph"""

    nodes: Optional[List[GraphNode]]
    sel: SelectorMultiplexer

    def __repr__(self) -> str:
        return "Graph[" + "\n".join(repr(n) for n in self.nodes) + "]"

    def is_dag(self) -> bool:
        """Decide if the given gn is a Directed Acyclic Graph"""
        try:
            for _ in self._is_dag():
                pass
            return True
        except AssertionError:
            return False

    def _is_dag(self) -> List["GraphNode"]:
        """Returns a list of nodes with 0 source from gn and removes it from other's src list"""
        copied = deepcopy(self)

        while copied.nodes:
            next_nodes = [n for n in copied.nodes if len(n.src) == 0]
            copied.nodes = [n for n in copied.nodes if len(n.src) > 0]
            assert (
                len(next_nodes) == 0 and len(copied.nodes) > 0
            ) is False, "Not a DAG, the graph contains a circle."
            for copied_node in copied.nodes:
                for to_remove_node in next_nodes:
                    copied_node.src = [
                        n
                        for n in copied_node.src
                        if n.node.id != to_remove_node.node.id
                    ]
            yield [n for n in self.nodes if n in next_nodes]

    def is_connected(self) -> bool:
        """find out if the graph is connected"""

        def dfs(node):
            visited.add(node)
            for neighbor in adjacency_list[node]:
                if neighbor not in visited:
                    dfs(neighbor)

        if not self.nodes:
            return True  # Empty graph is considered connected

        visited = set()
        adjacency_list = {n: [] for n in self.nodes}

        for node in self.nodes:
            for src in node.src:
                adjacency_list[src].append(node)

        start_node = list(adjacency_list.keys())[0]
        dfs(start_node)

        return len(visited) == len(self.nodes)

    def iter_next_nodes(self) -> List["GraphNode"]:
        """Returns a list of nodes with 0 source from gn and removes it from other's src list"""
        copied = deepcopy(self)
        # visited = set()
        failed = set()

        while True:
            node_cnt_before = len(copied.nodes)
            # find all nodes with in degree 0 and but not in failed
            next_nodes = [
                n for n in copied.nodes if len(n.src) == 0 and n not in failed
            ]
            # get it from thie original graph
            to_yield = [n for n in self.nodes if n in next_nodes]
            # yield it
            indes = yield to_yield
            # visited.update(next_nodes)
            if indes:
                # add it to visited
                failed.update(next_nodes[i] for i in indes)

            # remove all 0 in degree node
            copied.nodes = [n for n in copied.nodes if len(n.src) > 0 or n in failed]

            # remove all processed nodes from the downstream src list
            for copied_node in copied.nodes:
                for to_remove_node in set(next_nodes) - failed:
                    copied_node.src = [
                        n
                        for n in copied_node.src
                        if n.node.id != to_remove_node.node.id
                    ]

            if node_cnt_before == len(copied.nodes):
                # if the graph size not shrink
                break


class ExecutionContext(BaseModel):
    outputs: Dict[str, Any] = Field({})


class ExecutionException(Exception):
    pass

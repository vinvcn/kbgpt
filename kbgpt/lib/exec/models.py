from collections import namedtuple
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class CheckerMod(BaseModel):
    type: Literal["type"]
    key: str


class InListCheckerMod(CheckerMod):
    type: Literal["in_list"] = Field("in_list")
    trg_list: Optional[List[Any]]


class EqCheckerMod(CheckerMod):
    type: Literal["eq"] = Field("eq")
    trg_value: Optional[Any]


class EvalCheckerMod(CheckerMod):
    type: Literal["eval"] = Field("eval")
    eval_exp: str


class EngineMod(BaseModel):
    type: Literal["engine"]
    # out_keys: List[str]

    def __repr__(self) -> str:
        return f"Engine:{self.type}"


class MapperEngineMod(EngineMod):
    type: Literal["mapper_engine"]
    mapping: Dict[str, Any]


class EmbedEngineMod(EngineMod):
    type: Literal["embed_engine"] = Field("embed_engine")
    key_and_labels: Dict[str, str]


class SimilaritySearchMod(EngineMod):
    type: Literal["similarity_search_engine"] = Field("similarity_search_engine")
    index: str
    k: int
    min_threshold: Optional[float]


class TemplateEngineMod(EngineMod):
    type: Literal["template_engine"]
    stream: bool = Field(False)
    keys_in: List[str]
    models: List[str]
    name: str


class SimpleEngineMod(TemplateEngineMod):
    type: Literal["simple_engine"] = Field("simple_engine")


class JinjaEngineMod(TemplateEngineMod):
    type: Literal["jinja_engine"] = Field("jinja_engine")


class CommentEngineMod(EngineMod):
    type: Literal["comment_engine"]
    name: str


class ReportEngineMod(EngineMod):
    type: Literal["report_engine"] = Field("report_engine")
    name: str
    render_config: Dict[str, Any]


class ToVoiceEngineMod(EngineMod):
    type: Literal["to_voice_engine"]


class TestEngineMod(EngineMod):
    type: Literal["test_engine"] = Field("test_engine")
    input_keys: List[str] = Field([])
    output: Dict[str, Any] = Field({})


class Selector(BaseModel):
    node: str = Field("")
    key: str = Field("")
    to_key: str = Field("")

    class Config:
        frozen = True

    def with_to_key(self, to_key: str):
        return self.copy(update={"to_key": to_key})


class MultiplexerType(Enum):
    ALL = "all"
    SOME = "some"
    FIRST = "first"


class SelectorMultiplexer(BaseModel):
    selectors: List[Selector]
    mode: MultiplexerType = Field(MultiplexerType.ALL)


class Expression(BaseModel):
    def eval(self):
        pass


class Condition(Expression):
    value: Any

    def eval(self):
        return self.value


EngineTypes = Union[
    ToVoiceEngineMod,
    ReportEngineMod,
    CommentEngineMod,
    SimpleEngineMod,
    EmbedEngineMod,
    JinjaEngineMod,
    SimilaritySearchMod,
    MapperEngineMod,
    TestEngineMod,
]

_CheckerTypes = Union[InListCheckerMod, EqCheckerMod, EvalCheckerMod]

CheckerTypes = Union[_CheckerTypes, List[_CheckerTypes]]


class Node(BaseModel):
    engine: Optional[EngineTypes] = Field(None, discriminator="type")
    id: str
    frm: Optional[SelectorMultiplexer]
    sel: Dict[str, str] = Field({})
    pre: Optional[CheckerTypes]
    post: Optional[CheckerTypes]

    # pylint: disable = E0213:no-self-argument
    @validator("id", pre=True)
    def validate_id(val):
        """validate id field"""
        if not val:
            return str(uuid4())
        else:
            return val

    def __repr__(self) -> str:
        return f"Node[id:{self.id},engine:{repr(self.engine)}]"

    @property
    def selectors(self):
        if self.engine.out_keys:
            Selectors = namedtuple("Selectors", self.engine.out_keys)
            return Selectors(
                *[Selector(node=self.id, key=k) for k in self.engine.out_keys]
            )


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

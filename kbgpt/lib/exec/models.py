from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class EngineMod(BaseModel):
    type: Literal["engine"]


class MapperEngineMod(EngineMod):
    type: Literal["mapper_engine"]
    mapping: Dict[str, Any]


class SimpleEngineMod(EngineMod):
    type: Literal["simple_engine"]
    name: str


class CommentEngineMod(EngineMod):
    type: Literal["comment_engine"]
    name: str


class ReportEngineMod(EngineMod):
    type: Literal["report_engine"]
    name: str
    render_config: Dict[str, Any]


class ToVoiceEngineMod(EngineMod):
    type: Literal["to_voice_engine"]


class Addresser(BaseModel):
    node: str
    key: str

    class Config:
        frozen = True


class Node(BaseModel):
    engine: Union[
        ToVoiceEngineMod,
        ReportEngineMod,
        CommentEngineMod,
        SimpleEngineMod,
        MapperEngineMod,
    ] = Field(..., discriminator="type")
    id: str
    frm: Optional[Dict[Addresser, str]]
    sel: Optional[Dict[str, str]]

    @validator("id", pre=True)
    def validate_id(self, val):
        """validate id field"""
        if not val:
            return str(uuid4())
        else:
            return val


class GraphNode(BaseModel):
    node: Optional[Node]
    to: List["GraphNode"]

    @staticmethod
    def is_dag(node: "GraphNode", visited=None, recursion_stack=None) -> bool:
        if visited is None:
            visited = set()
        if recursion_stack is None:
            recursion_stack = set()

        visited.add(node)
        recursion_stack.add(node)

        for neighbor in node.to:
            if neighbor not in visited:
                if GraphNode.is_dag(neighbor, visited, recursion_stack):
                    return False
            elif neighbor in recursion_stack:
                return False

        recursion_stack.remove(node)
        return True

from typing import Any, Dict, Literal

from pydantic import BaseModel


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

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class EngineMod(BaseModel):
    type: Literal["engine"]
    # out_keys: List[str]

    def __repr__(self) -> str:
        return f"Engine:{self.type}"


class MapperMod(EngineMod):
    type: Literal["mapper_engine"]
    mapping: Dict[str, Any]


class EmbedMod(EngineMod):
    type: Literal["embed_engine"] = Field("embed_engine")
    key_and_labels: Dict[str, str]


class SimilaritySearchMod(EngineMod):
    type: Literal["similarity_search_engine"] = Field("similarity_search_engine")
    index: str
    k: int
    min_threshold: Optional[float]


class TemplateMod(EngineMod):
    type: Literal["template_engine"]
    stream: bool = Field(False)
    keys_in: List[str]
    models: List[str]
    name: str


class SimpleMod(TemplateMod):
    type: Literal["simple_engine"] = Field("simple_engine")


class JinjaMod(TemplateMod):
    type: Literal["jinja_engine"] = Field("jinja_engine")


class TestMod(EngineMod):
    type: Literal["test_engine"] = Field("test_engine")
    input_keys: List[str] = Field([])
    output: Dict[str, Any] = Field({})


EngineTypes = Union[
    SimpleMod,
    EmbedMod,
    JinjaMod,
    SimilaritySearchMod,
    MapperMod,
    TestMod,
]

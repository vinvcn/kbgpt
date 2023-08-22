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


class OutputMod(EngineMod):
    type: Literal["output_engine"] = Field("output_engine")


class RecomOutTransMod(EngineMod):
    type: Literal["recomm_transform"] = Field("recomm_transform")


class QAOutputMod(OutputMod):
    type: Literal["qa_output"] = Field("qa_output")
    stream: bool = Field(False)


class RecomOutMod(OutputMod):
    type: Literal["recomm_output"] = Field("recomm_output")
    stream: bool = Field(False)


EngineTypes = Union[
    SimpleMod,
    EmbedMod,
    JinjaMod,
    SimilaritySearchMod,
    MapperMod,
    TestMod,
    QAOutputMod,
    RecomOutTransMod,
    RecomOutMod,
]

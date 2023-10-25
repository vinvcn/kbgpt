from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

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


class PersistLevel(Enum):
    NONE = "none"
    DEBUG = "debug"
    INFO = "info"


class SemanticCache(Enum):
    NONE = "none"
    REDIS = "redis"


class ClientStyle(Enum):
    NATIVE = "native"
    ROUNDROBIN = "roundrobin"


class CacheMod(BaseModel):
    enabled: bool = Field(False)
    query_key: str = Field("question")
    clear_on_init: bool = Field(False)
    index_name: Optional[str]


class ClassificationMod(EngineMod):
    type: Literal["classification_engine"] = Field("classification_engine")
    model: str
    client_style: str = Field(ClientStyle.NATIVE.value)
    temperature: float = Field(0.0)
    mapping: Dict[int, str]
    cache: Optional[CacheMod]


class TemplateMod(EngineMod):
    type: Literal["template_engine"]
    stream: bool = Field(False)
    temperature: float = Field(0.0)
    keys_in: List[str]
    models: Tuple[str, ...]
    name: str
    persist_level: str = Field(PersistLevel.INFO.value)
    client_style: str = Field(ClientStyle.NATIVE.value)
    cache: Optional[CacheMod]


class SimpleMod(TemplateMod):
    type: Literal["simple_engine"] = Field("simple_engine")


class JinjaMod(TemplateMod):
    type: Literal["jinja_engine"] = Field("jinja_engine")


class GraphExecMod(EngineMod):
    type: Literal["graph_exec"] = Field("graph_exec")
    graph: Optional[Any]


class TestMod(EngineMod):
    type: Literal["test_engine"] = Field("test_engine")
    input_keys: List[str] = Field([])
    output: Dict[str, Any] = Field({})


class OutputMod(EngineMod):
    type: Literal["output_engine"] = Field("output_engine")


class RecomOutTransMod(EngineMod):
    type: Literal["recomm_transform"] = Field("recomm_transform")
    max_output: Optional[int] = Field(4)


class QAOutputMod(OutputMod):
    type: Literal["qa_output"] = Field("qa_output")
    stream: bool = Field(False)


class RecomOutMod(OutputMod):
    type: Literal["recomm_output"] = Field("recomm_output")
    stream: bool = Field(False)


class FunctionOutMod(OutputMod):
    type: Literal["function_output"] = Field("function_output")
    stream: bool = Field(False)


EngineTypes = Union[
    SimpleMod,
    EmbedMod,
    JinjaMod,
    GraphExecMod,
    SimilaritySearchMod,
    ClassificationMod,
    MapperMod,
    TestMod,
    QAOutputMod,
    FunctionOutMod,
    RecomOutTransMod,
    RecomOutMod,
]

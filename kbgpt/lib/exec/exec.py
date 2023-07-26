from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field
from sanic import Sanic

from kbgpt.lib.exec import engine_factory
from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.models import (
    CommentEngineMod,
    MapperEngineMod,
    ReportEngineMod,
    SimpleEngineMod,
    ToVoiceEngineMod,
)


class NodeEval:
    async def aeval(self, ctx: Dict[str, Any], node: "Node", params: Dict[str, Any]):
        factory: engine_factory = ctx["factory"]
        await node.validate_input(**params)
        engine: Engine = factory.create_from_model(node.engine)
        oup = await engine.agenerate(**params)
        return oup


class Mapper(BaseModel):
    type: Literal["mapper"]

    def map_ou_to(self, ou_obj: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def map_in_to(self, in_obj: Dict[str, Any]) -> Dict[str, Any]:
        pass


class Selector(BaseModel):
    type: Literal["selector"]

    def select(self, **params):



class Mapper(BaseModel):
    type: Literal["mapper"]

class RenameMapper(BaseModel):
    type: Literal["rename_mapper"]

    in_mapping: Dict[str, str]
    ou_mapping: Dict[str, str]

    def map_ou_to(self, ou_obj: Dict[str, Any]) -> Dict[str, Any]:
        return self._map_to(ou_obj, self.ou_mapping)

    def map_in_to(self, in_obj: Dict[str, Any]) -> Dict[str, Any]:
        return self._map_to(in_obj, self.in_mapping)

    def _map_to(self, obj: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        renamed = {}
        for k, v in mapping:
            renamed[v] = obj[k]

        restof = {k: v for k, v in obj.items() if k not in mapping}
        return {**renamed, **restof}


class Node(BaseModel):
    engine: Union[
        ToVoiceEngineMod,
        ReportEngineMod,
        CommentEngineMod,
        SimpleEngineMod,
        MapperEngineMod,
    ] = Field(..., discriminator="type")
    pass_through: bool = Field(True)
    in_selector: 
    in_keys: Optional[List[str]]
    # mapper: Optional[Union[RenameMapper, Mapper]] = Field(None, discriminator="type")

    async def validate_input(self, **kwargs):
        if any([k not in kwargs for k in self.in_keys]):
            raise ValueError(" key not in input keys")


class SerialPipe(BaseModel):
    nodes: List["Node"]

    async def aexec(self, seed: Dict[str, Any], engine_factory: engine_factory):
        ctx: Dict[str, Any] = {"factory": engine_factory}
        evaluator = NodeEval()
        inputs = [seed]
        outputs = []
        for node in self.nodes:
            inp = inputs[-1]
            oup = await evaluator.aeval(ctx, node, inp)
            outputs.append(oup)
            inputs.append(oup)

        return outputs

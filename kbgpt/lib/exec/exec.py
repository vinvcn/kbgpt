from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

from kbgpt.lib.exec import engine_factory
from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.models import Addresser, Node


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
        pass


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


class ExecutionContext(BaseModel):
    outputs: Optional[Dict["Addresser", Any]]
    # seed: Optional[Dict[str, Any]]


class NodeExecutor:
    node: Node
    enginefact: engine_factory.EngineFactory

    async def exec(self, ctx: ExecutionContext):
        # create engine from config
        engine = self.enginefact.create_from_model(self.node.engine)
        # prepare input values
        engine_in = {targ: ctx.outputs[addr] for addr, targ in self.node.frm}
        # execute the engine
        engine_out = await engine.agenerate(**engine_in)
        # save output to context
        for k, v in engine_out.items():
            ctx.outputs[
                Addresser(node=f"{self.node.engine.type}_{self.node.id}", key=k)
            ] = v


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

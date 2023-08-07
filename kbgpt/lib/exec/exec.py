import asyncio
import json
import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from kbgpt.lib.exec import engine_factory
from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.models import Graph, GraphNode, Node, Selector, SelectorTypes
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.templates.rendering.models import TemplateRepo


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
    outputs: Dict[str, Any] = Field({})


class SelectorExec:
    selectors: SelectorTypes

    def __init__(self, selectors: SelectorTypes) -> None:
        self.selectors = selectors

    async def exec(self, ctx: ExecutionContext):
        output_dict = {}
        if not self.selectors:
            return output_dict

        if isinstance(self.selectors, Selector):
            self.selectors = [self.selectors]

        for selector in self.selectors:
            if selector.to_key:
                assert (
                    selector.to_key not in output_dict
                ), f"output key '{selector.to_key}' conflict"
                output_dict[selector.to_key] = ctx.outputs[selector.node][selector.key]
            else:
                assert (
                    selector.key not in output_dict
                ), f"default output key '{selector.key}' conflict"
                output_dict[selector.key] = ctx.outputs[selector.node][selector.key]

        return output_dict

    # seed: Optional[Dict[str, Any]]


class NodeExecutor:
    node: GraphNode
    enginefact: engine_factory.EngineFactory

    def __init__(self, node: GraphNode) -> None:
        self.node = node
        self.enginefact = engine_factory.EngineFactory(TemplateFactory().create())

    # async def validate(self):
    #     prepare_params = {}
    #     if self.node.src:
    #         for src_node in self.node.src:

    async def exec(self, ctx: ExecutionContext):
        """execute the node iteself"""
        # create engine from config
        engine = self.enginefact.create_from_model(self.node.node.engine)
        # prepare input values
        # prepare_params = {}
        # for selector in self.node.node.frm:
        #     prepare_params[selector.to_key] = ctx.outputs[selector.node][selector.key]

        # if not self.node.src:
        #     # source nodes, add all seed's keys
        #     prepare_params = ctx.seed.copy()
        # else:
        #     for src_node in self.node.src:
        #         src_out = ctx.outputs[src_node.id]
        #         for sel_key, as_key in src_node.node.sel.items():
        #             assert (
        #                 as_key not in prepare_params
        #             ), f"key {as_key} conflict in preparing params"
        #             prepare_params[as_key] = src_out[sel_key]

        # logging.debug("mapping selected params")
        # engine_in = prepare_params.copy()
        # if self.node.node.frm:
        #     for k, v in prepare_params.items():
        #         for mk, mv in self.node.node.frm.items():
        #             if mk == k:
        #                 del engine_in[k]
        #                 engine_in[mv] = v

        engine_in = await SelectorExec(self.node.node.frm).exec(ctx)
        # check for precondition
        # for k in engine_in:
        #     self.node.node.pre

        # execute the engine
        engine_out = await engine.agenerate(**engine_in)

        logging.debug("map keys for output")
        engine_result = engine_out.copy()
        for f_k, to_k in self.node.node.sel.items():
            if f_k in engine_out:
                del engine_result[f_k]
                engine_result[to_k] = engine_out[f_k]

        # check for postcondition

        # save output to context
        ctx.outputs[self.node.id] = engine_result
        logging.info("execution done for node:\n%s", self.node)
        logging.info("inputs:\n%s", json.dumps(engine_in, indent=4))
        logging.info("outputs:\n%s", json.dumps(engine_result, indent=4))


class GraphExecutor:
    graph: Graph

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    async def exec(self, seed: Dict[str, Any] = dict()):
        """executes the given graph"""
        ctx = ExecutionContext(outputs={"seed": seed.copy()})

        try:
            assert (
                self.graph.is_connected() and self.graph.is_dag()
            ), "graph should be a connected DAG."
            for ls_nodes in self.graph.iter_next_nodes():
                logging.info("executing nodes %s", "\n".join(repr(n) for n in ls_nodes))
                await asyncio.gather(
                    *[NodeExecutor(node=n).exec(ctx) for n in ls_nodes]
                )

            logging.debug("execution done, preparing output...")

            output_dict = await SelectorExec(self.graph.sel).exec(ctx)

            logging.info(
                "graph execution completes, result context:\n%s", ctx.json(indent=4)
            )
            logging.info("outputs:\n%s", json.dumps(output_dict))
            return output_dict
        except Exception as e:
            logging.exception(e)
            raise e


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

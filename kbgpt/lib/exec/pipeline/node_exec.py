import logging

import kbgpt.lib.exec.engines.factory
from kbgpt.lib.exec.pipeline.checker_exec import CheckerExec, CheckerFailedException
from kbgpt.lib.exec.pipeline.checker_factory import CheckerFactory
from kbgpt.lib.exec.pipeline.graph_models import (
    ExecutionContext,
    GraphNode,
    NodeException,
)
from kbgpt.lib.exec.pipeline.selector_exec import SelectorExec
from kbgpt.lib.exec.template_factory import TemplateFactory


class NodeExecutor:
    def __init__(self, node: GraphNode) -> None:
        self.node = node
        self.enginefact = kbgpt.lib.exec.engines.factory.CORE_FACTORY
        self.checkerfact = CheckerFactory()

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

        try:
            engine_in, _ = await SelectorExec(self.node.node.frm).exec(ctx)
            # check for precondition
            await CheckerExec(self.node.node.pre).exec(engine_in)

            # execute the engine
            # engine_out = await engine.agenerate(**engine_in, ctx=ctx)
            engine_out = await engine.agenerate(
                **engine_in, invoke_id=ctx.invoke_id, envs=ctx.envs
            )

            logging.debug("map keys for output")
            engine_result = engine_out.copy()
            for f_k, to_k in self.node.node.sel.items():
                if f_k in engine_out:
                    del engine_result[f_k]
                    engine_result[to_k] = engine_out[f_k]

            # check for postcondition
            await CheckerExec(self.node.node.post).exec(engine_in)

            # save output to context
            ctx.outputs[self.node.id] = engine_result
            logging.info("execution done for node:\n%s", self.node)
            # logging.info("inputs:\n%s", json.dumps(engine_in, indent=4))
            # logging.info("outputs:\n%s", json.dumps(engine_result, indent=4))
        except CheckerFailedException as e:
            raise e
        except Exception as e:
            raise NodeException(f"Exception while executing node {self.node.id}") from e

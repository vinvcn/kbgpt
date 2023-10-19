import asyncio
import json
import logging
from typing import Any, Dict

from kbgpt.lib.exec.pipeline.checker_exec import CheckerFailedException
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import (
    ExecutionContext,
    ExecutionException,
    Graph,
)
from kbgpt.lib.exec.pipeline.node_exec import NodeExecutor
from kbgpt.lib.exec.pipeline.selector_exec import SelectorExec

from .selector_exec import SelectorExec


class GraphExecutor:
    graph: Graph

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    async def exec(
        self,
        seed: Dict[str, Any] = dict(),
        envs: Dict[str, Any] = dict(),
        invoke_id: str = None,
    ):
        """executes the given graph"""
        ctx = ExecutionContext(
            outputs={K_SEED: seed.copy()}, envs=envs, invoke_id=invoke_id
        )

        try:
            assert (
                self.graph.is_connected() and self.graph.is_dag()
            ), "graph should be a connected DAG."

            try:
                nodes_gen = self.graph.iter_next_nodes()
                excepts = None
                while True:
                    ls_nodes = nodes_gen.send(excepts)
                    logging.info(
                        "executing nodes %s", "\n".join(repr(n) for n in ls_nodes)
                    )
                    node_results = await asyncio.gather(
                        *[NodeExecutor(node=n).exec(ctx) for n in ls_nodes],
                        return_exceptions=True,
                    )

                    exception_nodes = [
                        (rst, nod)
                        for rst, nod in zip(node_results, ls_nodes)
                        if isinstance(rst, Exception)
                        and not isinstance(rst, CheckerFailedException)
                    ]

                    excepts = [
                        node_results[i]
                        for i, r in enumerate(node_results)
                        if isinstance(r, Exception)
                        and not isinstance(r, CheckerFailedException)
                    ]
                    if exception_nodes:
                        raise ExecutionException(
                            f"execution encountered exceptions for node {[nod.node.id for _, nod in exception_nodes]}",
                            [exp for exp, _ in exception_nodes],
                        )

                    excepts = [
                        i
                        for i, r in enumerate(node_results)
                        if isinstance(r, CheckerFailedException)
                    ]

            except StopIteration:
                pass

            logging.debug("execution done, preparing output...")

            output_dict, _ = await SelectorExec(self.graph.sel).exec(ctx)

            logging.debug(
                "graph execution completes, result context:\n%s", ctx.outputs.keys()
            )
            logging.debug("output keys:\n%s", output_dict.keys())
            return output_dict
        except Exception as e:
            raise e

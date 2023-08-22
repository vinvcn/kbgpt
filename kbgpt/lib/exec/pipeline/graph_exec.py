import asyncio
import json
import logging
from typing import Any, Dict

from kbgpt.lib.exec.pipeline.checker_exec import CheckerFailedException
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

    async def exec(self, seed: Dict[str, Any] = dict()):
        """executes the given graph"""
        ctx = ExecutionContext(outputs={"seed": seed.copy()})

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
                    excepts = [
                        i
                        for i, r in enumerate(node_results)
                        if isinstance(r, Exception)
                        and not isinstance(r, CheckerFailedException)
                    ]
                    if excepts:
                        raise ExecutionException(
                            f"execution encountered exceptions for node {ls_nodes[excepts[0]]}"
                        ) from node_results[excepts[0]]

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
            logging.debug("outputs:\n%s", json.dumps(output_dict))
            return output_dict
        except Exception as e:
            logging.exception(e)
            raise e

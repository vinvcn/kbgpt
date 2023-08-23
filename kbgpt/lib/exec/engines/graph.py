from typing import Any, Dict

from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.engines.configs.models import GraphExecMod


class GraphExec(Engine):
    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        """generate the template"""
        from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor

        config: GraphExecMod = self.config
        return await GraphExecutor(config.graph).exec({**kwargs})

from functools import singledispatchmethod

from kbgpt.lib.exec.pipeline.graph_exec import GraphExecutor
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_exec import NodeExecutor


class ExecutorFactory:
    @singledispatchmethod
    def create_from_model(self, mod) -> GraphExecutor | NodeExecutor:
        ...

    @create_from_model.register
    def _(self, mod: Graph) -> GraphExecutor:
        return GraphExecutor(graph=mod)

    @create_from_model.register
    def _(self, mod: GraphNode) -> NodeExecutor:
        return NodeExecutor(node=mod)


EXEC_FACTORY = ExecutorFactory()

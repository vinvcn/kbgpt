from kbgpt.lib.exec.engines.configs.models import (
    ClassificationMod,
    GraphExecMod,
    JinjaMod,
)
from kbgpt.lib.exec.pipeline.graph_models import Graph


def get_cache_index_from_graph(graph: Graph):
    """get cache index from graph"""
    caches = []

    for nd in graph.nodes:
        if isinstance(nd.node.engine, GraphExecMod):
            caches.extend(get_cache_index_from_graph(nd.node.engine.graph))
    caches.extend(
        [
            n.node.engine.cache
            for n in graph.nodes
            if isinstance(n.node.engine, JinjaMod)
        ]
    )

    caches.extend(
        [
            n.node.engine.cache
            for n in graph.nodes
            if isinstance(n.node.engine, ClassificationMod)
        ]
    )

    return caches

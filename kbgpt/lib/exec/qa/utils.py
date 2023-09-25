from kbgpt.lib.exec.pipeline.graph_models import Graph


def get_cache_index_from_graph(graph: Graph):
    caches = [
        n.node.engine.cache for n in graph.nodes if n.node.engine.type == "jinja_engine"
    ]

    index_names = [c.index_name for c in caches if c]
    return index_names

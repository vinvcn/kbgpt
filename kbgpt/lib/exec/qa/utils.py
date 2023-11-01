import importlib
import inspect
import os
from re import U

from async_lru import alru_cache

from kbgpt.lib.exec.engines.configs.models import (
    ClassificationMod,
    DecisionMod,
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
            if isinstance(n.node.engine, DecisionMod)
        ]
    )

    return caches


def find_methods_with_annotation(cls, annotation):
    methods = []

    for name, method in inspect.getmembers(cls, inspect.ismethod):
        if (
            hasattr(method, "__annotations__")
            and annotation in method.__annotations__.values()
        ):
            methods.append((name, method))

    return methods


def get_lru_cache_from_graph(graph: Graph):
    caches = []

    for nd in graph.nodes:
        if isinstance(nd.node.engine, GraphExecMod):
            caches.extend(get_lru_cache_from_graph(nd.node.engine.graph))

    for nd in graph.nodes:
        cached_methods = find_methods_with_annotation(nd.__class__, alru_cache)
        if cached_methods:
            caches.extend(cached_methods)

    return caches


def find_classes(directory):
    classes = []

    for root, dirs, files in os.walk(directory):
        print(root)
        for file in files:
            if file.endswith(".py"):
                module_name = os.path.splitext(file)[0]
                module_path = root.replace(".", "").replace("/", ".")

                try:
                    if module_name == "__init__":
                        continue
                    print(module_name)
                    module = importlib.import_module(module_name, module_path)

                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj):
                            classes.append(obj)

                except ImportError:
                    pass

    return classes

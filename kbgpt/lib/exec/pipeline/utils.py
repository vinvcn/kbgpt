from kbgpt.lib.exec.engines.configs.models import (
    CacheMod,
    FunctionOutMod,
    GraphExecMod,
    JinjaMod,
    OutputMod,
    QAOutputMod,
    RecomOutMod,
    TemplateMod,
)
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode, TriggerMode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)
from kbgpt.svc.aigc.qa.qa_graph_fetch_context import CONTEXT_GRAPH
from kbgpt.svc.aigc.qa.qa_graph_wizout_tailor import RECOMMEND_GRAPH


def create_nodes_and_update_callbacks(local_items):
    nodes = [v for k, v in local_items if isinstance(v, GraphNode)]

    for nod in [node.node for node in nodes]:
        engine = nod.engine
        if isinstance(engine, TemplateMod):
            if engine.stream:
                engine.keys_in.append("callbacks")
                nod.frm.selectors.append(Selector(node=K_SEED, key="callbacks"))
        if isinstance(engine, OutputMod):
            if engine.stream:
                nod.frm.selectors.append(Selector(node=K_SEED, key="callbacks"))
        if isinstance(engine, GraphExecMod):
            nod.frm.selectors.append(Selector(node=K_SEED, key="callbacks"))

    return nodes

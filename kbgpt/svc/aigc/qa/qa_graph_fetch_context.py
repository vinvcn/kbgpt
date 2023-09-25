from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    CacheMod,
    EmbedMod,
    JinjaMod,
    SimilaritySearchMod,
)
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import Selector, SelectorMultiplexer


def fetch_context_graph():
    embed_ques = GraphNode(
        node=Node(
            id="embed_question",
            engine=EmbedMod(key_and_labels={"question": ""}),
            frm=SelectorMultiplexer(selectors=[Selector(node=K_SEED, key="question")]),
        ),
        src=[],
    )

    search_context = GraphNode(
        node=Node(
            id="search_context",
            engine=SimilaritySearchMod(
                index=profile.qa.redis_index,
                k=profile.vector_store.vector_retrival_k,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="embed_question", key="result", to_key="embedding")
                ]
            ),
        ),
        src=[embed_ques],
    )

    is_context_related = GraphNode(
        node=Node(
            id="is_context_related",
            engine=JinjaMod(
                name="qa.is_context_related",
                keys_in=["question", "context"],
                models=[profile.generative_model, profile.qa.generative_model],
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:is_context_related",
                ),
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node="search_context", key="result", to_key="context"),
                ]
            ),
        ),
        src=[search_context],
    )

    graph = Graph(
        nodes=[embed_ques, search_context, is_context_related],
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="embed_question", key="result", to_key="embedding"),
                Selector(node="search_context", key="result", to_key="context"),
                Selector(node="is_context_related", key="result", to_key="is_related"),
            ]
        ),
    )
    return graph


CONTEXT_GRAPH = fetch_context_graph()

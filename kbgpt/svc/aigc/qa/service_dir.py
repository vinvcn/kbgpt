from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    CacheMod,
    ClassificationMod,
    ClientStyle,
    EmbedMod,
    JinjaMod,
    SimilaritySearchMod,
)
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import Selector, SelectorMultiplexer
from kbgpt.lib.exec.pipeline.utils import create_nodes_and_update_callbacks


def service_dir():
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

    search_amc = GraphNode(
        node=Node(
            id="search_amc",
            engine=SimilaritySearchMod(
                index=profile.amc_catalog.redis_index_name,
                k=profile.amc_catalog.product_retrieval_k,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="embed_question", key="result", to_key="embedding")
                ]
            ),
        ),
        src=[embed_ques],
    )

    search_amc_qa = GraphNode(
        node=Node(
            id="search_amc_qa",
            engine=SimilaritySearchMod(
                index=profile.amc_catalog.redis_qa_index_name,
                k=profile.amc_catalog.product_retrieval_k,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="embed_question", key="result", to_key="embedding")
                ]
            ),
        ),
        src=[embed_ques],
    )

    search_product = GraphNode(
        node=Node(
            id="search_product",
            engine=SimilaritySearchMod(
                index=profile.product_catalog.redis_index_name,
                k=profile.product_catalog.product_retrieval_k,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="embed_question", key="result", to_key="embedding")
                ]
            ),
        ),
        src=[embed_ques],
    )

    select_service_directory_item = GraphNode(
        node=Node(
            id="select_service_directory_item",
            engine=ClassificationMod(
                model="gpt-3.5-turbo",
                mapping={
                    1: "Customer question is unrelated.",
                    2: "Customer question has an accurate match in Knowledge list",
                    3: "Customer mentioned a product in the Product list.",
                    4: "Customer mentioned an AMC in the AMC list.",
                    5: "Customer question is about AMC in general.",
                    6: "The answer can be found in About Bullsmart.",
                    7: "The answer can be inferred by information in Knowledge list.",
                    8: "Customer question hits Recommend Condition.",
                    9: "The question is redated to the field of business of Bullsmart.",
                },
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:select_service_directory_item",
                    clear_on_init=True,
                ),
                client_style=ClientStyle.ROUNDROBIN.value,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node="embed_question", key="result", to_key="embedding"),
                    Selector(node="search_context", key="result", to_key="context"),
                    Selector(node="search_amc", key="result", to_key="amc"),
                    Selector(node="search_product", key="result", to_key="product"),
                ]
            ),
        ),
        src=[search_context, search_amc, search_product],
    )
    nodes = create_nodes_and_update_callbacks(locals().items())

    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="search_context", key="result", to_key="context"),
                Selector(node="search_amc", key="result", to_key="amc"),
                Selector(node="search_amc_qa", key="result", to_key="amc_qa"),
                Selector(node="search_product", key="result", to_key="product"),
                Selector(node="embed_question", key="result", to_key="embedding"),
                Selector(
                    node="select_service_directory_item",
                    key="result",
                    to_key="action",
                ),
            ]
        ),
    )

    return graph


CLASS_GRAPH = service_dir()

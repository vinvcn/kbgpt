from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    CacheMod,
    ClientStyle,
    DecisionTreeMod,
    DTreeNode,
    EmbedMod,
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
            engine=DecisionTreeMod(
                model="gpt-3.5-turbo",
                rst_regex="^[^:]*",
                root=DTreeNode(
                    template="classification.classification_with_trigger_mf_recommendation",
                    mapping=[
                        ("Function", "Customer question meets condition in Function."),
                        ("Others", "None of the above."),
                    ],
                    children={
                        "Others": DTreeNode(
                            template="classification.classification_with_context_and_question",
                            mapping=[
                                (
                                    "Unrelated",
                                    "Customer question is irrelevant to our business.",
                                ),
                                (
                                    "Product",
                                    "It is possible to recommend a product",
                                ),
                                (
                                    "Product",
                                    "Customer is commanding to perform a service that's in the product list.",
                                ),
                                ("Knowledge", "Customer inquiry for information."),
                                (
                                    "Knowledge",
                                    "Customer mentioned something not existing.",
                                ),
                                (
                                    "Knowledge",
                                    "Customer question has an accurate match in Knowledge list",
                                ),
                                (
                                    "Knowledge",
                                    "The answer can be inferred by information in Knowledge list.",
                                ),
                                (
                                    "Knowledge",
                                    "The answer can be found in About Bullsmart.",
                                ),
                                ("AMC", "Customer mentioned an AMC in the AMC list."),
                                (
                                    "AMC_QA",
                                    "Customer question is about AMC in general.",
                                ),
                                ("Others", "None of the above."),
                            ],
                            children={},
                        )
                    },
                ),
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

    # select_service_directory_item = GraphNode(
    #     node=Node(
    #         id="select_service_directory_item",
    #         engine=DecisionTreeMod(
    #             model="gpt-3.5-turbo",
    #             rst_regex="^[^:]*",
    #             root=DTreeNode(
    #                 template="classification.trigger_qa_amc_product_others",
    #                 mapping=[
    #                     ("Unrelated", "Customer question is unrelated."),
    #                     (
    #                         "Product",
    #                         "Customer mentioned a product in the Product list.",
    #                     ),
    #                     (
    #                         "Knowledge",
    #                         "Customer question has an accurate match in Knowledge list",
    #                     ),
    #                     (
    #                         "Knowledge",
    #                         "The answer can be inferred by information in Knowledge list.",
    #                     ),
    #                     ("Knowledge", "The answer can be found in About Bullsmart."),
    #                     ("AMC", "Customer mentioned an AMC in the AMC list."),
    #                     ("AMC_QA", "Customer question is about AMC in general."),
    #                     ("Function", "Customer question meets condition in Function."),
    #                     ("Others", "None of the above."),
    #                 ],
    #             ),
    #             cache=CacheMod(
    #                 enabled=True,
    #                 query_key="question",
    #                 index_name=f"{profile.cache.customer_service_cache_index}:select_service_directory_item",
    #                 clear_on_init=True,
    #             ),
    #             client_style=ClientStyle.ROUNDROBIN.value,
    #         ),
    #         frm=SelectorMultiplexer(
    #             selectors=[
    #                 Selector(node=K_SEED, key="question"),
    #                 Selector(node="embed_question", key="result", to_key="embedding"),
    #                 Selector(node="search_context", key="result", to_key="context"),
    #                 Selector(node="search_amc", key="result", to_key="amc"),
    #                 Selector(node="search_product", key="result", to_key="product"),
    #             ]
    #         ),
    #     ),
    #     src=[search_context, search_amc, search_product],
    # )

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

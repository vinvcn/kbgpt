from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    EmbedMod,
    JinjaMod,
    RecomOutTransMod,
    SimilaritySearchMod,
)
from kbgpt.lib.exec.pipeline.checker_models import EvalCheckerMod
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import Selector, SelectorMultiplexer


def recommend_sub_graph():
    embed_question_answer_context = GraphNode(
        node=Node(
            id="embed_question_answer_context",
            engine=EmbedMod(
                key_and_labels={
                    "context": "Context",
                    "question": "Question",
                    "answer": "Answer",
                }
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(node="seed", key="context"),
                    Selector(
                        node="seed",
                        key="answer",
                    ),
                ]
            ),
        ),
        src=[],
    )

    search_products = GraphNode(
        node=Node(
            id="search_products",
            engine=SimilaritySearchMod(
                index=profile.product_catalog.redis_index_name,
                k=profile.product_catalog.product_retrieval_k,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="embed_question_answer_context",
                        key="result",
                        to_key="embedding",
                    ),
                ]
            ),
        ),
        src=[embed_question_answer_context],
    )

    tailor_products_before_recommendation = GraphNode(
        node=Node(
            id="tailor_products_before_recommendation",
            engine=JinjaMod(
                name="qa.recommend_tailor_products",
                keys_in=["question", "answer", "products", "context"],
                models=[profile.generative_model, profile.qa.generative_model],
                # models=profile.qa.recomm,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(
                        node="seed",
                        key="answer",
                    ),
                    Selector(node="seed", key="context"),
                    Selector(
                        node="search_products",
                        key="result",
                        to_key="products",
                    ),
                ]
            ),
        ),
        src=[search_products],
    )

    transform_recommend1 = GraphNode(
        node=Node(
            id="transform_recommend1",
            engine=RecomOutTransMod(max_output=30),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="tailor_products_before_recommendation",
                        key="result",
                        to_key="recomm",
                    ),
                    Selector(node="search_products", key="result", to_key="products"),
                ]
            ),
            pre=EvalCheckerMod(key="recomm", eval_exp="recomm.lower() != 'n/a'"),
        ),
        src=[tailor_products_before_recommendation],
    )

    recommend_products = GraphNode(
        node=Node(
            id="recommend_products",
            engine=JinjaMod(
                name="qa.recommend_products",
                keys_in=["question", "answer", "context", "products"],
                models=[profile.generative_model, profile.qa.generative_model],
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(
                        node="seed",
                        key="answer",
                    ),
                    Selector(node="seed", key="context"),
                    Selector(
                        node="transform_recommend1",
                        key="result",
                        to_key="products",
                    ),
                ]
            ),
        ),
        src=[transform_recommend1],
    )

    transform_recommend2 = GraphNode(
        node=Node(
            id="transform_recommend2",
            engine=RecomOutTransMod(),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="recommend_products", key="result", to_key="recomm"),
                    Selector(node="search_products", key="result", to_key="products"),
                ]
            ),
            pre=EvalCheckerMod(key="recomm", eval_exp="recomm.lower() != 'n/a'"),
        ),
        src=[recommend_products],
    )

    say_recommendation_hooks = GraphNode(
        node=Node(
            id="say_recommendation_hooks",
            engine=JinjaMod(
                name="qa.say_recommendation_hooks",
                keys_in=["question", "answer", "products", "callbacks"],
                models=[profile.generative_model, profile.qa.generative_model],
                stream=True,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(node="seed", key="callbacks"),
                    Selector(
                        node="seed",
                        key="answer",
                    ),
                    Selector(
                        node="transform_recommend2",
                        key="result",
                        to_key="products",
                    ),
                ]
            ),
        ),
        src=[transform_recommend2],
    )

    nodes = [v for k, v in locals().items() if isinstance(v, GraphNode)]
    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="transform_recommend2", key="result", to_key="products"),
                Selector(node="say_recommendation_hooks", key="result", to_key="hook"),
            ]
        ),
    )
    return graph

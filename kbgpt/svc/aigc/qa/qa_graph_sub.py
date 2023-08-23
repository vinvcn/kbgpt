from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    EmbedMod,
    JinjaMod,
    OutputMod,
    QAOutputMod,
    RecomOutMod,
    RecomOutTransMod,
    SimilaritySearchMod,
    TemplateMod,
)
from kbgpt.lib.exec.pipeline.checker_models import EvalCheckerMod
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode, TriggerMode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)


def fetch_context_graph():
    embed_ques = GraphNode(
        node=Node(
            id="embed_question",
            engine=EmbedMod(key_and_labels={"question": ""}),
            frm=SelectorMultiplexer(selectors=[Selector(node="seed", key="question")]),
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
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
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

    recommend_products = GraphNode(
        node=Node(
            id="recommend_products",
            engine=JinjaMod(
                name="qa.recommend_products",
                keys_in=["question", "answer", "context", "products"],
                models=profile.qa.recomm,
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

    transform_recommend = GraphNode(
        node=Node(
            id="transform_recommend",
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
                        node="transform_recommend",
                        key="result",
                        to_key="products",
                    ),
                ]
            ),
        ),
        src=[transform_recommend],
    )

    nodes = [v for k, v in locals().items() if isinstance(v, GraphNode)]
    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="transform_recommend", key="result", to_key="products"),
                Selector(node="say_recommendation_hooks", key="result", to_key="hook"),
            ]
        ),
    )
    return graph

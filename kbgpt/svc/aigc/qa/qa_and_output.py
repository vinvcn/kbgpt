from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    CacheMod,
    ClientStyle,
    GraphExecMod,
    JinjaMod,
    OutputMod,
    QAOutputMod,
    RecomOutMod,
    RecomOutTransMod,
    TemplateMod,
)
from kbgpt.lib.exec.pipeline.checker_models import EvalCheckerMod
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)
from kbgpt.lib.exec.pipeline.utils import create_nodes_and_update_callbacks


def qa_and_output_no_recomm(template, cache_index):
    """gen graph"""

    answer_without_context = GraphNode(
        node=Node(
            id="answer_without_context",
            engine=JinjaMod(
                name=template,
                keys_in=["question"],
                models=[profile.generative_model, profile.qa.generative_model],
                stream=True,
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:{cache_index}",
                ),
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node=K_SEED, key="embedding"),
                ]
            ),
        ),
        src=[],
    )

    answer_output = GraphNode(
        node=Node(
            id="answer_output",
            engine=QAOutputMod(stream=True),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="answer_without_context",
                        key="result",
                        to_key="answer",
                    )
                ],
                mode=MultiplexerType.ANY,
            ),
        ),
        src=[answer_without_context],
    )

    nodes = create_nodes_and_update_callbacks(locals().items())

    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(
                    node="answer_without_context",
                    key="result",
                    to_key="answer",
                ),
            ],
        ),
    )

    return graph


def qa_context_output_no_recomm():
    """doc"""
    answer_question_with_context = GraphNode(
        node=Node(
            id="answer_question_with_context",
            engine=JinjaMod(
                name="qa.answer_question_with_context",
                keys_in=["question", "context"],
                models=[profile.generative_model, profile.qa.generative_model],
                stream=True,
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:answer_question_with_context",
                ),
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node=K_SEED, key="context"),
                    Selector(node=K_SEED, key="embedding"),
                ]
            ),
        ),
        src=[],
    )

    answer_output = GraphNode(
        node=Node(
            id="answer_output",
            engine=QAOutputMod(stream=True),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    )
                ],
                mode=MultiplexerType.ANY,
            ),
        ),
        src=[answer_question_with_context],
    )
    nodes = create_nodes_and_update_callbacks(locals().items())

    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(
                    node="answer_question_with_context",
                    key="result",
                    to_key="answer",
                ),
            ],
        ),
    )

    return graph


def qa_and_output_graph():
    answer_question_with_context = GraphNode(
        node=Node(
            id="answer_question_with_context",
            engine=JinjaMod(
                name="qa.answer_question_with_context",
                keys_in=["question", "context"],
                models=[profile.generative_model, profile.qa.generative_model],
                stream=True,
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:answer_question_with_context",
                ),
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="product"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node=K_SEED, key="context"),
                    Selector(node=K_SEED, key="embedding"),
                ]
            ),
        ),
        src=[],
    )

    answer_output = GraphNode(
        node=Node(
            id="answer_output",
            engine=QAOutputMod(stream=True),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    )
                ],
                mode=MultiplexerType.ANY,
            ),
        ),
        src=[answer_question_with_context],
    )

    recommend_products = GraphNode(
        node=Node(
            id="recommend_products",
            engine=JinjaMod(
                name="qa.recommend_products",
                keys_in=["question", "answer", "context", "product"],
                models=[profile.generative_model, profile.qa.generative_model],
                client_style=ClientStyle.ROUNDROBIN.value,
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:recommend_products",
                ),
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    ),
                    Selector(node=K_SEED, key="context"),
                    Selector(node=K_SEED, key="embedding"),
                    Selector(
                        node=K_SEED,
                        key="product",
                    ),
                ]
            ),
        ),
        src=[answer_question_with_context],
    )

    transform_recommend2 = GraphNode(
        node=Node(
            id="transform_recommend2",
            engine=RecomOutTransMod(),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="recommend_products", key="result", to_key="recomm"),
                    Selector(
                        node=K_SEED,
                        key="product",
                        to_key="products",
                    ),
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
                cache=CacheMod(
                    enabled=True,
                    query_key="question",
                    index_name=f"{profile.cache.customer_service_cache_index}:say_recommendation_hooks",
                ),
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    ),
                    Selector(node=K_SEED, key="embedding"),
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

    recommend_output = GraphNode(
        node=Node(
            id="recommend_output",
            engine=RecomOutMod(stream=True),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="transform_recommend2", key="result", to_key="products"
                    ),
                    Selector(
                        node="say_recommendation_hooks", key="result", to_key="hook"
                    ),
                ],
                mode=MultiplexerType.NONE,
            ),
            pre=EvalCheckerMod(key="products", eval_exp="bool(products)"),
        ),
        src=[say_recommendation_hooks],
    )

    nodes = create_nodes_and_update_callbacks(locals().items())

    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(
                    node="answer_question_with_context",
                    key="result",
                    to_key="answer",
                ),
            ],
        ),
    )

    return graph


CONTEXT_QA_AND_OUTPUT = qa_and_output_graph()

CONTEXT_QA_NO_RECOMM = qa_context_output_no_recomm()

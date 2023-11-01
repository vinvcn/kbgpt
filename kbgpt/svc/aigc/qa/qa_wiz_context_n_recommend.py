from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    CacheMod,
    GraphExecMod,
    JinjaMod,
    OutputMod,
    QAOutputMod,
    RecomOutMod,
    TemplateMod,
)
from kbgpt.lib.exec.pipeline.checker_models import EvalCheckerMod
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode, TriggerMode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)
from kbgpt.lib.exec.pipeline.utils import create_nodes_and_update_callbacks
from kbgpt.svc.aigc.qa.qa_graph_fetch_context import CONTEXT_GRAPH
from kbgpt.svc.aigc.qa.qa_graph_wizout_tailor import RECOMMEND_GRAPH


def qa_graph():
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
                ]
            ),
        ),
        src=[],
    )

    make_recommendation_with_hooks = GraphNode(
        node=Node(
            id="make_recommendation_with_hooks",
            engine=GraphExecMod(graph=RECOMMEND_GRAPH),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="callbacks"),
                    Selector(node=K_SEED, key="context"),
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    ),
                ]
            ),
        ),
        src=[answer_question_with_context],
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
        trigger=TriggerMode.ANY,
    )

    recommend_output = GraphNode(
        node=Node(
            id="recommend_output",
            engine=RecomOutMod(stream=True),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(
                        node="make_recommendation_with_hooks",
                        key="products",
                    ),
                    Selector(
                        node="make_recommendation_with_hooks",
                        key="hook",
                    ),
                ],
                mode=MultiplexerType.NONE,
            ),
            pre=EvalCheckerMod(key="products", eval_exp="bool(products)"),
        ),
        src=[make_recommendation_with_hooks],
    )

    nodes = create_nodes_and_update_callbacks(locals().items())

    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(
                    node="answer_question_with_context", key="result", to_key="answer"
                ),
                Selector(
                    node="recommend_products", key="result", to_key="recommendation"
                ),
                Selector(node="say_recommendation_hooks", key="result", to_key="hook"),
            ],
            mode=MultiplexerType.ANY,
        ),
    )
    return graph


QA_GRAPH = qa_graph()

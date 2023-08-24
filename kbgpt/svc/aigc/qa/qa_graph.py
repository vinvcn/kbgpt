from config import profile
from kbgpt.lib.exec.engines.configs.models import (
    EmbedMod,
    GraphExecMod,
    JinjaMod,
    OutputMod,
    QAOutputMod,
    RecomOutMod,
    RecomOutTransMod,
    SimilaritySearchMod,
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
from kbgpt.svc.aigc.qa.qa_graph_fetch_context import fetch_context_graph
from kbgpt.svc.aigc.qa.qa_graph_recommendation import recommend_sub_graph


def qa_graph():
    fetch_context_n_is_related = GraphNode(
        node=Node(
            id="fetch_context_n_is_related",
            engine=GraphExecMod(graph=fetch_context_graph()),
            frm=SelectorMultiplexer(selectors=[Selector(node=K_SEED, key="question")]),
        ),
        src=[],
    )

    answer_without_context = GraphNode(
        node=Node(
            id="answer_without_context",
            engine=JinjaMod(
                name="qa.answer_without_context",
                keys_in=["question"],
                models=[profile.generative_model, profile.qa.generative_model],
                stream=True,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node="fetch_context_n_is_related", key="is_related"),
                ]
            ),
            pre=EvalCheckerMod(key="is_related", eval_exp="is_related.lower() == 'no'"),
        ),
        src=[fetch_context_n_is_related],
    )

    answer_question_with_context = GraphNode(
        node=Node(
            id="answer_question_with_context",
            engine=JinjaMod(
                name="qa.answer_question_with_context",
                keys_in=["question", "context"],
                models=[profile.generative_model, profile.qa.generative_model],
                stream=True,
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node="fetch_context_n_is_related", key="context"),
                    Selector(node="fetch_context_n_is_related", key="is_related"),
                ]
            ),
            pre=EvalCheckerMod(
                key="is_related", eval_exp="is_related.lower() == 'yes'"
            ),
        ),
        src=[fetch_context_n_is_related],
    )

    make_recommendation_with_hooks = GraphNode(
        node=Node(
            id="make_recommendation_with_hooks",
            engine=GraphExecMod(graph=recommend_sub_graph()),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="callbacks"),
                    Selector(node="fetch_context_n_is_related", key="context"),
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
                    ),
                    Selector(
                        node="answer_without_context",
                        key="result",
                        to_key="answer",
                    ),
                ],
                mode=MultiplexerType.ANY,
            ),
        ),
        src=[answer_question_with_context, answer_without_context],
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
                ]
            ),
        ),
        src=[make_recommendation_with_hooks],
    )

    nodes = [v for k, v in locals().items() if isinstance(v, GraphNode)]

    for nod in [node.node for node in nodes]:
        engine = nod.engine
        if isinstance(engine, TemplateMod):
            if engine.stream:
                engine.keys_in.append("callbacks")
                nod.frm.selectors.append(Selector(node=K_SEED, key="callbacks"))
        if isinstance(engine, OutputMod):
            if engine.stream:
                nod.frm.selectors.append(Selector(node=K_SEED, key="callbacks"))

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
                Selector(node="answer_without_context", key="result", to_key="answer"),
            ],
            mode=MultiplexerType.ANY,
        ),
    )
    return graph


QA_GRAPH = qa_graph()

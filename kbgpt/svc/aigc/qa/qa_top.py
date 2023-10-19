from config import profile
from kbgpt.lib.exec.engines.configs.models import CacheMod, GraphExecMod, JinjaMod
from kbgpt.lib.exec.pipeline.checker_models import EvalCheckerMod, InListCheckerMod
from kbgpt.lib.exec.pipeline.constants import K_SEED
from kbgpt.lib.exec.pipeline.graph_models import Graph, GraphNode
from kbgpt.lib.exec.pipeline.node_models import Node
from kbgpt.lib.exec.pipeline.selector_models import (
    MultiplexerType,
    Selector,
    SelectorMultiplexer,
)
from kbgpt.lib.exec.pipeline.utils import create_nodes_and_update_callbacks
from kbgpt.svc.aigc.qa.qa_and_output import (
    CONTEXT_QA_AND_OUTPUT,
    qa_and_output_no_recomm,
)
from kbgpt.svc.aigc.qa.recommend_product import RECOMMEND_GRAPH
from kbgpt.svc.aigc.qa.service_dir import CLASS_GRAPH


def qa_top():
    classify_actions = GraphNode(
        node=Node(
            id="classify_actions",
            engine=GraphExecMod(graph=CLASS_GRAPH),
            frm=SelectorMultiplexer(selectors=[Selector(node=K_SEED, key="question")]),
        ),
        src=[],
    )

    ask_clarification_question = GraphNode(
        node=Node(
            id="ask_clarification_question",
            engine=GraphExecMod(
                graph=qa_and_output_no_recomm(
                    "qa.ask_clarification_question", "ask_clarification_question"
                )
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node="classify_actions", key="context"),
                    Selector(node="classify_actions", key="action"),
                    Selector(node="classify_actions", key="product"),
                    Selector(node="classify_actions", key="embedding"),
                ]
            ),
            pre=InListCheckerMod(key="action", trg_list=["5"]),
        ),
        src=[classify_actions],
    )

    qa_random_chat = GraphNode(
        node=Node(
            id="qa_random_chat",
            engine=GraphExecMod(
                graph=qa_and_output_no_recomm(
                    "qa.answer_without_context", "qa_random_chat"
                )
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node="classify_actions", key="context"),
                    Selector(node="classify_actions", key="action"),
                    Selector(node="classify_actions", key="product"),
                    Selector(node="classify_actions", key="embedding"),
                ]
            ),
            pre=InListCheckerMod(key="action", trg_list=["1"]),
        ),
        src=[classify_actions],
    )

    context_qa_and_output = GraphNode(
        node=Node(
            id="context_qa_and_output",
            engine=GraphExecMod(graph=CONTEXT_QA_AND_OUTPUT),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node="classify_actions", key="context"),
                    Selector(node="classify_actions", key="action"),
                    Selector(node="classify_actions", key="product"),
                    Selector(node="classify_actions", key="embedding"),
                ]
            ),
            pre=InListCheckerMod(key="action", trg_list=["2", "6", "7"]),
        ),
        src=[classify_actions],
    )

    recommend_and_output = GraphNode(
        node=Node(
            id="recommend_and_output",
            engine=GraphExecMod(graph=RECOMMEND_GRAPH),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="question", to_key="answer"),
                    Selector(node="classify_actions", key="context"),
                    Selector(node="classify_actions", key="product"),
                    Selector(node="classify_actions", key="action"),
                    Selector(node="classify_actions", key="embedding"),
                ]
            ),
            pre=EvalCheckerMod(key="action", eval_exp="action == '3'"),
        ),
        src=[classify_actions],
    )

    search_amc_catalog = GraphNode(
        node=Node(
            id="search_amc_catalog",
            engine=GraphExecMod(graph=CONTEXT_QA_AND_OUTPUT),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node=K_SEED, key="question"),
                    Selector(node=K_SEED, key="words_limit"),
                    Selector(node="classify_actions", key="amc", to_key="context"),
                    Selector(node="classify_actions", key="action"),
                    Selector(node="classify_actions", key="product"),
                    Selector(node="classify_actions", key="embedding"),
                ]
            ),
            pre=EvalCheckerMod(key="action", eval_exp="action == '4'"),
        ),
        src=[classify_actions],
    )

    nodes = create_nodes_and_update_callbacks(locals().items())

    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(node="ask_clarification_question", key="answer"),
                Selector(node="qa_random_chat", key="answer"),
                Selector(node="context_qa_and_output", key="answer"),
                Selector(node="recommend_and_output", key="answer"),
                Selector(node="search_amc_catalog", key="answer"),
            ],
            mode=MultiplexerType.NONE,
        ),
    )
    return graph


QA_TOP_GRAPH = qa_top()

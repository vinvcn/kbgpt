import pytest

from config import profile
from kbgpt.lib.exec.engines import Embed, SimilaritySearch, SimpleEngine
from kbgpt.lib.exec.exec import GraphExecutor
from kbgpt.lib.exec.models import (
    EmbedEngineMod,
    EqCheckerMod,
    EvalCheckerMod,
    Graph,
    GraphNode,
    MultiplexerType,
    Node,
    Selector,
    SelectorMultiplexer,
    SimilaritySearchMod,
    SimpleEngineMod,
)


@pytest.fixture
def qa_graph():
    embed_ques = GraphNode(
        node=Node(
            id="embed_question",
            engine=EmbedEngineMod(key_and_labels={"question": ""}),
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
            engine=SimpleEngineMod(
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

    answer_without_context = GraphNode(
        node=Node(
            id="answer_without_context",
            engine=SimpleEngineMod(
                name="qa.answer_without_context",
                keys_in=["question"],
                models=[profile.generative_model, profile.qa.generative_model],
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(
                        node="is_context_related", key="result", to_key="is_related"
                    ),
                ]
            ),
            pre=EvalCheckerMod(key="is_related", eval_exp="is_related.lower() == 'no'"),
        ),
        src=[is_context_related],
    )

    answer_question_with_context = GraphNode(
        node=Node(
            id="answer_question_with_context",
            engine=SimpleEngineMod(
                name="qa.answer_question_with_context",
                keys_in=["question", "context"],
                models=[profile.generative_model, profile.qa.generative_model],
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(node="seed", key="words_limit"),
                    Selector(node="search_context", key="result", to_key="context"),
                    Selector(
                        node="is_context_related", key="result", to_key="is_related"
                    ),
                ]
            ),
            pre=EvalCheckerMod(
                key="is_related", eval_exp="is_related.lower() == 'yes'"
            ),
        ),
        src=[is_context_related],
    )

    nodes = [
        embed_ques,
        search_context,
        is_context_related,
        answer_without_context,
        answer_question_with_context,
    ]
    graph = Graph(
        nodes=nodes,
        sel=SelectorMultiplexer(
            selectors=[
                Selector(
                    node="answer_question_with_context", key="result", to_key="answer"
                ),
                Selector(node="answer_without_context", key="result", to_key="answer"),
            ],
            mode=MultiplexerType.SOME,
        ),
    )
    return graph


@pytest.mark.asyncio
async def test_qa_chain(qa_graph):
    result = await GraphExecutor(qa_graph).exec(
        {"question": "what is bullsmart?", "words_limit": 38}
    )
    assert "answer" in result and "bullsmart" in result["answer"].lower()

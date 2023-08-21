from config import profile
from kbgpt.lib.exec.models import (
    EmbedEngineMod,
    EvalCheckerMod,
    Graph,
    GraphNode,
    JinjaEngineMod,
    MultiplexerType,
    Node,
    Selector,
    SelectorMultiplexer,
    SimilaritySearchMod,
    SimpleEngineMod,
    TemplateEngineMod,
)


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
            engine=JinjaEngineMod(
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
            engine=JinjaEngineMod(
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

    embed_question_answer_context = GraphNode(
        node=Node(
            id="embed_question_answer_context",
            engine=EmbedEngineMod(
                key_and_labels={
                    "context": "Context",
                    "question": "Question",
                    "answer": "Answer",
                }
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(node="search_context", key="result", to_key="context"),
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
            engine=JinjaEngineMod(
                name="qa.recommend_products",
                keys_in=["question", "answer", "context", "products"],
                models=[profile.generative_model, profile.qa.generative_model],
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    ),
                    Selector(node="search_context", key="result", to_key="context"),
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

    say_recommendation_hooks = GraphNode(
        node=Node(
            id="say_recommendation_hooks",
            engine=JinjaEngineMod(
                stream=True,
                name="qa.say_recommendation_hooks",
                keys_in=["question", "answer", "products"],
                models=[profile.generative_model, profile.qa.generative_model],
            ),
            frm=SelectorMultiplexer(
                selectors=[
                    Selector(node="seed", key="question"),
                    Selector(
                        node="answer_question_with_context",
                        key="result",
                        to_key="answer",
                    ),
                    Selector(
                        node="search_products",
                        key="result",
                        to_key="products",
                    ),
                ]
            ),
        ),
        src=[recommend_products],
    )

    nodes = [
        embed_ques,
        search_context,
        is_context_related,
        answer_without_context,
        answer_question_with_context,
        embed_question_answer_context,
        search_products,
        recommend_products,
        say_recommendation_hooks,
    ]

    for nod in [node.node for node in nodes]:
        engine = nod.engine
        if isinstance(engine, TemplateEngineMod):
            if engine.stream:
                engine.keys_in.append("callbacks")
                nod.frm.selectors.append(Selector(node="seed", key="callbacks"))

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
            mode=MultiplexerType.SOME,
        ),
    )
    return graph

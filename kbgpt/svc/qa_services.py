"""
QA agents
"""
import abc
import logging
import threading
import time
from functools import wraps
from typing import List, Tuple

from langchain import PromptTemplate
from langchain.callbacks import (
    AsyncCallbackManager,
    BaseCallbackHandler,
    CallbackManager,
    OpenAICallbackHandler,
)
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.base import Chain
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.vector_store import (
    create_vector_store_strategy,
    get_embeddings,
)
from kbgpt.lib.openai import chat_open_ai_llm

RULES = (
    "You should strictly follow the following rules:\n"
    "- only use information from the context and no prior knowledge.\n"
    "- You should provide super details that you found from the context, only if it's related to the question.\n"
    "- Be friendly and considerable.\n"
    "- Put the answer in HTML format.\n"
    "- Be straight and precise.\n"
    f"- Limit the answer to within {profile.qa.words_limit} words.\n"
)


class Context:
    """
    context for wrapping agent calls
    """

    def __init__(self) -> None:
        self.cache_hit = False

    def cached(self):
        """query the cache store"""
        that = self

        def wrapper(func):
            if not profile.cache.use_redis_cache:
                return func
            else:
                # only when cache is set to true
                @wraps(
                    func
                )  # wraps the function to provide the original docstring
                async def wrapped(self, question, *args, **kwargs):
                    cache = RedisCacheStoreStrategy.get_instance(
                        embeddings=get_embeddings()
                    )
                    cached = await cache.retrieve(query=question)
                    if cached:
                        that.cache_hit = True
                        return cached["answer"], OpenAICallbackHandler()
                    else:
                        that.cache_hit = False
                        result, stats = await func(
                            self, question=question, *args, **kwargs
                        )
                        await cache.write_to_store(
                            question=question, answer=result
                        )
                        return result, stats

                return wrapped

        return wrapper


context = Context()


class AbstractAgent(metaclass=abc.ABCMeta):
    """
    Abstract class for all agents
    """

    __lock = threading.Lock()

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """
        Get the instance of the agent
        """
        if not hasattr(cls, "instance"):
            with cls.__lock:
                if not hasattr(cls, "instance"):
                    cls(*args, **kwargs)
        return cls.instance

    def __init__(self) -> None:
        if hasattr(AbstractAgent, "instance"):
            raise ValueError("This class is a singleton!")
        else:
            super().__init__()
            self.k = profile.vector_store.vector_retrival_k
            self.vector_store_cls = profile.vector_store.vector_store_class
            AbstractAgent.instance = self

    @abc.abstractmethod
    def load_chain(self, llm: ChatOpenAI) -> BaseCombineDocumentsChain:
        """
        Load the chain for the agent
        """

    @context.cached()
    async def answer_question(
        self, question: str
    ) -> Tuple[str, OpenAICallbackHandler]:
        """
        Answer a question as a customer service agent"""
        # if profile.cache.use_redis_cache:
        #     cache = RedisCacheStoreStrategy.get_instance(
        #         embeddings=get_embeddings()
        #     )
        #     cached = await cache.retrieve(query=question)
        #     if cached:
        #         return cached["answer"], None
        logging.debug("Started answering question: %s", question)
        start_counter = time.perf_counter()
        answer, stats = await self.answer_question_and_provide_cost(
            question=question
        )
        logging.debug(
            "End of answering question: %s, total time %.3f seconds",
            question,
            time.perf_counter() - start_counter,
        )
        logging.info("Total token consumed: %s", stats.total_tokens)
        logging.info("Total cost: %s", stats.total_cost)
        # if profile.cache.use_redis_cache:
        #     await cache.write_to_store(question=question, answer=answer)
        return answer, stats

    async def answer_question_and_provide_cost(
        self, question: str
    ) -> Tuple[str, OpenAICallbackHandler]:
        """
        Answer a question as a customer service agent and provide the cost of the answer
        """
        stats = OpenAICallbackHandler()
        llm = chat_open_ai_llm(handlers=[stats])
        start_counter = time.perf_counter()
        logging.debug("Started loading vector store")
        retriever = create_vector_store_strategy().get_retriever(k=self.k)
        logging.debug(
            "End of loading vector store, total time %.3f seconds",
            time.perf_counter() - start_counter,
        )

        logging.debug(
            "Started retrieving relevant documents for question: %s", question
        )
        start_counter = time.perf_counter()
        result1 = retriever.get_relevant_documents(query=question)
        logging.debug(
            "%s Documents retrieved, total time %.3f seconds",
            len(result1),
            time.perf_counter() - start_counter,
        )

        logging.debug("Started loading chain")
        start_counter = time.perf_counter()
        chain = self.load_chain(llm)
        logging.debug(
            "End of loading chain, total time %.3f seconds",
            time.perf_counter() - start_counter,
        )

        logging.debug("Started running chain")
        start_counter = time.perf_counter()
        value = await chain.acall(
            {"input_documents": result1, "question": question}
        )
        # chain.prep_outputs
        logging.debug(
            "End of running chain, total time %.3f seconds",
            time.perf_counter() - start_counter,
        )
        return value["output_text"], stats


class QAagent(AbstractAgent):
    """
    Agent that can refine an existing answer"""

    def load_chain(self, llm: ChatOpenAI) -> BaseCombineDocumentsChain:
        """
        Load the stuff chain for the customer service agent"""
        prompt_template = (
            "Pretend you are a customer service representative for an mobile App called Bullsmart. You were provided the following Context information.\n"
            "---------------------\n"
            "{context}"
            "\n---------------------\n"
            "Given the context information and not prior knowledge, "
            "answer the question in markdown: {question}\n"
            f"{RULES}"
        )

        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        chain = load_qa_chain(
            llm, chain_type="stuff", verbose=True, prompt=PROMPT
        )
        return chain


class RefineAgent(AbstractAgent):
    """
    Agent that can refine an existing answer"""

    def load_chain(self, llm: ChatOpenAI) -> BaseCombineDocumentsChain:
        """
        Load the QA chain for the customer service agent"""

        refine_prompt_template = (
            "Pretend you are a customer service representative for an mobile App called Bullsmart. The original question is as follows: {question}\n"
            "We have provided an existing answer: {existing_answer}\n"
            "We have the opportunity to refine the existing answer"
            "(only if needed) with some more context below.\n"
            "------------\n"
            "{context_str}\n"
            "------------\n"
            "Given the new context information and the original answer, "
            "refine the original answer in markdown to better answer the question.\n"
            f"{RULES}"
            "If the context isn't useful, return the original answer."
        )
        refine_prompt = PromptTemplate(
            input_variables=["question", "existing_answer", "context_str"],
            template=refine_prompt_template,
        )

        initial_qa_template = (
            "Pretend you are a customer service representative for an mobile App called Bullsmart. You were provided the following Context information.\n"
            "---------------------\n"
            "{context_str}"
            "\n---------------------\n"
            "Given the context information and not prior knowledge, "
            "answer the question in markdown: {question}\n"
            f"{RULES}"
        )
        initial_qa_prompt = PromptTemplate(
            input_variables=["context_str", "question"],
            template=initial_qa_template,
        )

        chain = load_qa_chain(
            llm,
            "refine",
            verbose=True,
            return_intermediate_steps=True,
            question_prompt=initial_qa_prompt,
            refine_prompt=refine_prompt,
        )
        return chain


class ConvAgent:
    """
    Conversational Agent
    """

    def __init__(self, handlers: List[BaseCallbackHandler], streaming, **data):
        super().__init__(**data)
        self.stats = OpenAICallbackHandler()
        handlers.extend([self.stats])
        llm = chat_open_ai_llm(handlers=handlers, streaming=streaming)
        retriever = create_vector_store_strategy().get_retriever(
            k=profile.vector_store.vector_retrival_k
        )
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=llm, retriever=retriever, callback_manager=CallbackManager([])
        )

    async def question(self, question: str):
        """
        Ask a question
        """
        result = self.chain({"question": question, "chat_history": ""})
        return result["answer"]


AGENT_STG = {
    "refine": RefineAgent,
    "stuff": QAagent,
    "builtin": ConversationalRetrievalChain,
}

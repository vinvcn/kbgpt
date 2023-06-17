"""
QA agents
"""
import abc
import logging
import threading
import time
from typing import List, Tuple

from langchain import PromptTemplate
from langchain.callbacks.manager import (
    BaseCallbackHandler,
    CallbackManager,
    OpenAICallbackHandler,
)
from kbgpt.svc.utils import get_total_cost
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage

from config import profile
from kbgpt.lib.db import Document
from kbgpt.lib.db.vector_store import create_vector_store_strategy
from kbgpt.lib.openai import chat_open_ai_llm

RULES = (
    "You should strictly follow the following rules:\n"
    "- If it is not a question, give a gentle and warm response.\n"
    "- Only use information from the context and no prior knowledge.\n"
    "- You should provide super details that you found from the context, only if it's related to the question.\n"
    "- Do not use any other information from the internet.\n"
    "- Be friendly and considerable.\n"
    "- Be straight and precise.\n"
    f"- Limit the answer to within {profile.qa.words_limit} words.\n"
    "- Do not add anything except for the answer for your customer.\n"
    "- Do not provide information other than the ones you find from the context.\n"
)

STUFF_TEMPLATE = (
    "Pretend you are a customer service representative for an mobile App called Bullsmart. You were provided the following Context information.\n"
    "---------------------\n"
    "{context}"
    "\n---------------------\n"
    f"{RULES}"
    "Given the context information and not prior knowledge, "
    "answer the question: {question}\n"
)


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

    async def answer_question(
        self, question: str, **kwargs
    ) -> Tuple[str, OpenAICallbackHandler]:
        """
        Answer a question as a customer service agent"""
        logging.debug("Started answering question: %s", question)
        start_counter = time.perf_counter()
        answer, stats = await self._answer_question_and_provide_cost(
            question=question, **kwargs
        )
        logging.debug(
            "End of answering question: %s, total time %.3f seconds",
            question,
            time.perf_counter() - start_counter,
        )
        logging.info("Total token consumed: %s", stats.total_tokens)
        logging.info("Total cost: %s", stats.total_cost)
        return answer, stats

    async def get_prompts_in_batch(
        self, questions: List[str], documents: List[List[Document]]
    ) -> List[str]:
        """get prompts in batch"""
        qes_n_docs = zip(questions, documents)
        inputs = [
            (ques, "\n".join([d.content for d in docs])) for ques, docs in qes_n_docs
        ]
        prompts = [
            STUFF_TEMPLATE.format(context=comb_doc, question=ques)
            for ques, comb_doc in inputs
        ]
        return prompts

    # async def answer_question_in_batch(
    #     self, questions: List[str], documents: List[List[Document]]
    # ) -> Tuple[List[str], OpenAICallbackHandler]:

    async def answer_question_in_batch(
            self, prompts: List[str]
    ) -> Tuple[List[str], OpenAICallbackHandler]:
        """
        Answer pairs of question and vectors in batch
        """
        stats = OpenAICallbackHandler()
        messages = [[SystemMessage(content=prompt)] for prompt in prompts]
        llm = chat_open_ai_llm(handlers=[stats])
        results = await llm.agenerate(messages)
        # see what's the result when http request failed
        return [gen[0].message.content for gen in results.generations], stats

    async def _answer_question_and_provide_cost(
        self, question: str, streaming: bool = False, callbacks=None
    ) -> Tuple[str, OpenAICallbackHandler]:
        """
        Answer a question as a customer service agent and provide the cost of the answer
        """
        stats = OpenAICallbackHandler()
        handlers = [stats]
        if callbacks:
            handlers.extend(callbacks)
        llm = chat_open_ai_llm(streaming=streaming, handlers=handlers)
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
        value = await chain.acall({"input_documents": result1, "question": question})
        # chain.prep_outputs
        logging.debug(
            "End of running chain, total time %.3f seconds",
            time.perf_counter() - start_counter,
        )
        if streaming:
            stats = OpenAICallbackHandler()
            total_cost = 0.0
            prompt_tokens = llm.get_num_tokens(question)
            completion_tokens = llm.get_num_tokens(value["output_text"])
            total_cost = get_total_cost(
                llm.model_name, prompt_tokens, completion_tokens
            )
            total_tokens = prompt_tokens + completion_tokens
            successful_requests = 1
            stats.prompt_tokens = prompt_tokens
            stats.completion_tokens = completion_tokens
            stats.total_tokens = total_tokens
            stats.total_cost = total_cost
            stats.successful_requests = successful_requests
        return value["output_text"], stats


class QAagent(AbstractAgent):
    """
    Agent that can refine an existing answer"""

    def load_chain(self, llm: ChatOpenAI) -> BaseCombineDocumentsChain:
        """
        Load the stuff chain for the customer service agent"""

        PROMPT = PromptTemplate(
            template=STUFF_TEMPLATE, input_variables=["context", "question"]
        )
        chain = load_qa_chain(llm, chain_type="stuff", verbose=True, prompt=PROMPT)
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


AGENT_STG = {
    "refine": RefineAgent,
    "stuff": QAagent,
    "builtin": ConversationalRetrievalChain,
}

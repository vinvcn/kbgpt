import abc
from typing import Tuple

from langchain import PromptTemplate
from langchain.callbacks import CallbackManager, OpenAICallbackHandler
from langchain.chains import ConversationChain
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis

from config import *
from kbgpt.lib.templates.file_qa_template import FileQATemplate

RULES = (
    "You should strictly follow the following rules:\n"
    "- only use information from the context and no prior knowledge.\n"
    "- You should provide super details that you found from the context, only if it's related to the question.\n"
    "- Be friendly and considerable.\n"
    "- Find all the valid URLs, embed it in the relavent part in your answer as links. [<description>](url)\n"
    "- Find all the valid image URLs, embed it in the relatent part in your answer as  image. e.g. ![<image description>](url)\n"
    "- The answer is in markdown format.\n"
)


class AbstractAgent(metaclass=abc.ABCMeta):
    """
    Abstract class for all agents
    """

    def __init__(self, k=1) -> None:
        self.k = k

    @abc.abstractmethod
    def load_chain(self, llm: ChatOpenAI) -> BaseCombineDocumentsChain:
        """
        Load the chain for the agent"""
        pass

    def answer_question(self, question: str) -> str:
        """
        Answer a question as a customer service agent"""
        answer, stats = self.answer_question_and_provide_cost(question=question)

        return answer

    def answer_question_and_provide_cost(self, question: str) -> Tuple[str, OpenAICallbackHandler]:
        """
        Answer a question as a customer service agent and provide the cost of the answer
        """
        stats = OpenAICallbackHandler()
        llm = ChatOpenAI(
            model_name=GENERATIVE_MODEL,
            n=1,
            temperature=CUSTOMER_SERVICE_TEMPERATURE,
            max_tokens=1000,
            callback_manager=CallbackManager([stats]),
        )

        rds = Redis.from_existing_index(
            redis_url=REDIS_URL,
            index_name=CUSTOMER_SERVICE_INDEX,
            embedding=OpenAIEmbeddings(),
        ).as_retriever(k=self.k)

        # result1 = rds.similarity_search(query=question, k=2)
        result1 = rds.get_relevant_documents(query=question)  # , k=2)

        chain = self.load_chain(llm)

        value = chain({"input_documents": result1, "question": question})

        return value["output_text"], stats


class QAagent(AbstractAgent):
    """
    Agent that can refine an existing answer"""

    def __init__(self, k=1) -> None:
        super().__init__(k)

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

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(llm, chain_type="stuff", verbose=True, prompt=PROMPT)
        return chain


class RefineAgent(AbstractAgent):
    """
    Agent that can refine an existing answer"""

    def __init__(self, k=3) -> None:
        super().__init__(k)

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
        initial_qa_prompt = PromptTemplate(input_variables=["context_str", "question"], template=initial_qa_template)

        chain = load_qa_chain(
            llm,
            "refine",
            verbose=True,
            return_intermediate_steps=True,
            question_prompt=initial_qa_prompt,
            refine_prompt=refine_prompt,
        )
        return chain

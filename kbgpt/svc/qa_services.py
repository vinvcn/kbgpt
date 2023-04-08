from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores.redis import Redis

from config import *
from kbgpt.lib.templates.file_qa_template import FileQATemplate

llm = OpenAI(model_name=GENERATIVE_MODEL, n=1, temperature=CUSTOMER_SERVICE_TEMPERATURE, max_tokens=1000)


def answer_question_as_a_customer_service_agent(question: str) -> str:
    vector_retriever = Redis.from_existing_index(
        redis_url=REDIS_URL,
        index_name=CUSTOMER_SERVICE_INDEX,
        embedding=OpenAIEmbeddings(),
    ).as_retriever()

    result1 = vector_retriever.get_relevant_documents(question)

    llm_result = llm(
        FileQATemplate(input_variables=["documents", "question_str"]).format(documents=result1, question_str=question)
    )
    return llm_result

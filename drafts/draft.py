import json

from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.output_parsers import RegexParser
from langchain.vectorstores.redis import Redis

from config import *
from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import answer_question_as_a_customer_service_agent

# add_file_to_customer_service("/Users/admin/Desktop/About Us.docx")
# output_parser = RegexParser(
#     regex=r"(.*?)\nScore: ([0-9]*)",
#     output_keys=["answer", "score"],
# )

# prompt_template = """You are a customer service representative for a financial service App called Bullsmart. Use the following pieces of Context to answer the question at the end.

# Context:
# ---------
# {context}
# ---------

# Follow these rules when talking to your customer:

# - If the Context contains no related information, say "I don't know".
# - Don't provide information that is not in the Context. If you can not find an answer just say "I don't know". and give a 0 score.
# - Do not make up information which is not present in the Context.
# - Be friendly and polite.
# - Provide super details and context to your answer.
# - Organize the response into a easy to read format.


# In addition to giving an answer, also return a score of how truthfully it answered the user's question. This should be in the following format:

# Question: [question here]
# Context: [context here]
# Helpful Answer: [answer here]
# Score: [score between 0 and 100]

# Begin!


# Question: {question}
# Helpful Answer:"""

# PROMPT = PromptTemplate(
#     template=prompt_template,
#     input_variables=["context", "question"],
#     output_parser=output_parser,
# )

refine_prompt_template = (
    "Pretend you are a customer service representative for an mobile App called Bullsmart. The original question is as follows: {question}\n"
    "We have provided an existing answer: {existing_answer}\n"
    "We have the opportunity to refine the existing answer"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{context_str}\n"
    "------------\n"
    "Given the new context information and the original answer, "
    "refine the original answer to better answer the question. You should strictly follow the rule to only use information from the context and no prior knowledge. You should provide super details that you found from the context, only if it's related to the question. Be friendly and considerable. \n"
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
    "answer the question: {question}\n You should strictly follow the rule to only use information from the context and no prior knowledge. You should provide super details that you found from the context, only if it's related to the question. Be friendly and considerable. \n"
)
initial_qa_prompt = PromptTemplate(input_variables=["context_str", "question"], template=initial_qa_template)


llm = ChatOpenAI(model_name=GENERATIVE_MODEL, n=1, temperature=CUSTOMER_SERVICE_TEMPERATURE, max_tokens=1000)
redis = Redis.from_existing_index(
    redis_url=REDIS_URL,
    index_name=CUSTOMER_SERVICE_INDEX,
    embedding=OpenAIEmbeddings(),
)
question = "What is the best way to contact Bullsmart?"
docs = redis.similarity_search_limit_score(question, score_threshold=0.2)
chain = load_qa_chain(
    llm,
    "refine",
    verbose=True,
    return_intermediate_steps=True,
    question_prompt=initial_qa_prompt,
    refine_prompt=refine_prompt,
)  # , prompt=PROMPT)

value = chain({"input_documents": docs, "question": question})
print(json.dumps(value, indent=4))

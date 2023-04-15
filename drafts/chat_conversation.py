from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.utilities import SerpAPIWrapper
from langchain.vectorstores.redis import Redis

from config import *
from kbgpt.lib.pompt import PREFIX, SUFFIX

llm = ChatOpenAI(model_name=GENERATIVE_MODEL, n=1, temperature=CUSTOMER_SERVICE_TEMPERATURE, max_tokens=1000)

rds = Redis.from_existing_index(
    redis_url=REDIS_URL,
    index_name=CUSTOMER_SERVICE_INDEX,
    embedding=OpenAIEmbeddings(),
).as_retriever()

tools = [
    Tool(
        name="Search",
        func=lambda x: "\n\n".join(d.page_content for d in rds.get_relevant_documents(query=x)),
        description="useful for when you need to answer questions about Bullsmart and AMC. the input to this should be a single search term.",
    )
]

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

llm = ChatOpenAI(temperature=0)
agent_chain = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    agent_kwargs={"system_message": PREFIX, "human_message": SUFFIX},
)


while True:
    txt = input("Enter a question: ")
    agent_chain.run(input=txt)

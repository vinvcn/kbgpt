import os

os.environ["LANGCHAIN_HANDLER"] = "langchain"

from langchain import LLMMathChain, OpenAI
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis

from config import profile

llm = ChatOpenAI(temperature=0, verbose=True)
llm1 = OpenAI(temperature=0)

llm_math_chain = LLMMathChain(llm=llm1, verbose=True)
rds = Redis.from_existing_index(
    redis_url=profile.vector_store.redis_url,
    index_name=profile.indexing.customer_service_index,
    embedding=OpenAIEmbeddings(),
).as_retriever(k=3)
tools = [
    Tool(
        name="Search",
        func=lambda x: "\n\n".join(
            d.page_content for d in rds.get_relevant_documents(query=x)
        ),
        description="useful for when you need to answer questions. the input to this should be a single search term.",
    )
]

mrkl = initialize_agent(
    tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)

while True:
    txt = input("Enter a question: ")
    try:
        mrkl.run(txt)
    except ValueError as e:
        raise e

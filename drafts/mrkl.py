from langchain import LLMMathChain, OpenAI
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.redis import Redis

from config import profile

llm = OpenAI(temperature=0)

llm_math_chain = LLMMathChain(llm=llm, verbose=True)

rds = Redis.from_existing_index(
    redis_url=profile.vector_store.redis_url,
    index_name=profile.indexing.customer_service_index,
    embedding=OpenAIEmbeddings(),
).as_retriever()

tools = [
    Tool(
        name="Bullsmart Search",
        func=lambda x: "\n\n".join(
            d.page_content for d in rds.get_relevant_documents(query=x)
        ),
        description="useful for when you need to answer questions about Bullsmart. the input to this should be a single search term.",
    ),
    Tool(
        name="AMC Search",
        func=lambda x: "\n\n".join(
            d.page_content for d in rds.get_relevant_documents(query=x)
        ),
        description="useful for when you need to answer questions about AMC. the input to this should be a single search term.",
    ),
    Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="useful for when you need to answer questions about math",
    ),
]

mrkl = initialize_agent(
    tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)


while True:
    txt = input("Enter a question: ")
    mrkl.run(txt)

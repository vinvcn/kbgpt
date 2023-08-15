from langchain.chains import GraphQAChain
from langchain.document_loaders import TextLoader
from langchain.indexes import GraphIndexCreator
from langchain.llms import OpenAI

index_creator = GraphIndexCreator(llm=OpenAI(temperature=0))

with open("/Users/admin/Projects/kbgpt/kbgpt/res/productsintent.csv") as f:
    all_text = f.read()

graph = index_creator.from_text(all_text)

chain = GraphQAChain.from_llm(OpenAI(temperature=0), graph=graph, verbose=True)
chain.run("what is Intel going to build?")

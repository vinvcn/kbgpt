from langchain.text_splitter import TokenTextSplitter
from langchain.vectorstores import Chroma
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings


def run():
    # with open('./kbgpt/resource/baima.txt') as f:
    #     state_of_the_union = f.read()
    # text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=100)
    # texts = text_splitter.split_text(state_of_the_union)

    index_creator = VectorstoreIndexCreator(
        vectorstore_cls=Chroma, 
        embedding=OpenAIEmbeddings(),
        text_splitter=TokenTextSplitter(chunk_size=1000, chunk_overlap=100)
    )

    # print(texts)
    # loader = TextLoader('./kbgpt/resource/baima.txt')
    # index = VectorstoreIndexCreator().from_loaders([loader])
    # index.query('白马')



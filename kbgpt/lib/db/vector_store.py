import abc
import os
from typing import List, Optional

import pinecone
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import Chroma, Pinecone
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores.redis import Redis
from pydantic import BaseModel

from config import *


class VectorStoreStrategy(BaseModel, metaclass=abc.ABCMeta):
    """
    Abstract class for vector store strategies
    """

    index_name: str = CUSTOMER_SERVICE_INDEX

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(VectorStoreStrategy, cls).__new__(cls)
        return cls.instance

    @abc.abstractmethod
    async def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        """
        Get the retriever
        """
        pass

    @abc.abstractmethod
    async def write_to_store(self, documents: List[Document], flush_index=False, **kwargs) -> VectorStoreRetriever:
        """
        Write to the store
        """
        pass


class ChromaVectorStoreStrategy(VectorStoreStrategy):
    """
    Chroma vector store strategy
    """

    chroma: Optional[Chroma]
    embeddings: Optional[Embeddings]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, embeddings, **kwargs):
        super().__init__(embeddings=embeddings, **kwargs)
        self.chroma = Chroma(embedding_function=embeddings, persist_directory=CHROMA_PERSIST_DIR)

    async def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        # return self.chroma.as_retriever(search_kwargs={"k": k})
        return self.chroma.as_retriever(search_kwargs={"k": k})

    async def write_to_store(self, documents: List[Document], flush_index=False, **kwargs) -> VectorStoreRetriever:
        if flush_index:
            self.chroma.delete_collection()

        self.chroma = Chroma.from_documents(documents, embedding=self.embeddings, persist_directory=CHROMA_PERSIST_DIR)
        return self.chroma.as_retriever()


class PineConeVectorStoreStrategy(VectorStoreStrategy):
    """
    Pinecone vector store strategy"""

    api_key: str = os.environ["PINECONE_KEY"]
    environment: str = PINECONE_ENV

    def __init__(self, **kwargs):
        """
        Constructor"""
        super().__init__(**kwargs)
        pinecone.init(api_key=self.api_key, environment=self.environment)

    async def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        """
        Get the retriever
        """

        pc = Pinecone.from_existing_index(index_name=self.index_name, embedding=OpenAIEmbeddings())
        return pc.as_retriever(search_kwargs={"k": k})

    async def write_to_store(self, documents: List[Document], flush_index=False, **kwargs) -> VectorStoreRetriever:
        """
        Write to the store
        """

        try:
            pinecone.describe_index(self.index_name)
            if flush_index:
                pinecone.delete_index(self.index_name)
                pinecone.create_index(self.index_name, EMBEDDING_DIMENSIONS)
        except pinecone.exceptions.NotFoundException:
            pinecone.create_index(self.index_name, EMBEDDING_DIMENSIONS)

        pc = Pinecone.from_documents(documents, OpenAIEmbeddings(), index_name=self.index_name, api_key=self.api_key)

        return pc.as_retriever()


class RedisVectorStoreStrategy(VectorStoreStrategy):
    """
    Redis vector store strategy
    """

    redis_url: str = REDIS_URL

    async def get_retriever(self, k, **kwargs) -> VectorStoreRetriever:
        return Redis.from_existing_index(
            redis_url=self.redis_url, index_name=self.index_name, embedding=OpenAIEmbeddings()
        ).as_retriever(k=k)

    async def write_to_store(self, documents: List[Document], flush_index=False, **kwargs) -> VectorStoreRetriever:
        """
        Write to the store
        """

        if flush_index:
            Redis.drop_index(index_name=self.index_name, delete_documents=True, redis_url=self.redis_url)

        rds = Redis.from_documents(documents, OpenAIEmbeddings(), redis_url=self.redis_url, index_name=self.index_name)
        return rds.as_retriever(search_type="similarity_limit")


def get_embeddings() -> Embeddings:
    """
    Get the embeddings
    """
    embeddings: Embeddings = None
    if EMBEDDINGS_FUNCTION == "openai":
        embeddings = OpenAIEmbeddings()
    else:
        embeddings = None
    return embeddings


STORE_STG = {
    "redis": RedisVectorStoreStrategy,
    "pinecone": PineConeVectorStoreStrategy,
    "chroma": ChromaVectorStoreStrategy,
}


def create_vector_store_strategy(**kwargs) -> VectorStoreStrategy:
    """
    Create a vector store strategy
    """
    return STORE_STG[VECTOR_STORE_CLASS](embeddings=get_embeddings())

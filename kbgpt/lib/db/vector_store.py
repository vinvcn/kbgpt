import abc
import os
import threading
from typing import List

import pinecone
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import Chroma, Pinecone
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores.redis import Redis

from config import profile
from kbgpt.lib.openai import openai_embeddings


class VectorStoreStrategy(metaclass=abc.ABCMeta):
    """
    Abstract class for vector store strategies
    """

    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """
        Get the singleton instance
        """
        if not hasattr(cls, "instance"):
            with cls._lock:
                if not hasattr(cls, "instance"):
                    cls(*args, **kwargs)
        return cls.instance

    def __init__(self, embeddings: Embeddings) -> None:
        if hasattr(VectorStoreStrategy, "instance"):
            raise ValueError("An instantiation already exists!")
        else:
            super().__init__()
            self.embeddings = embeddings
            self.index_name = profile.indexing.customer_service_index
            VectorStoreStrategy.instance = self

    @abc.abstractmethod
    def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        """
        Get the retriever
        """

    @abc.abstractmethod
    async def write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        """
        Write to the store
        """


class ChromaVectorStoreStrategy(VectorStoreStrategy):
    """
    Chroma vector store strategy
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chroma = Chroma(
            embedding_function=self.embeddings,
            persist_directory=profile.vector_store.chroma_persist_dir,
        )

    def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        # return self.chroma.as_retriever(search_kwargs={"k": k})
        return self.chroma.as_retriever(search_kwargs={"k": k})

    async def write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        if flush_index:
            self.chroma.delete_collection()

        self.chroma = Chroma.from_documents(
            documents,
            embedding=self.embeddings,
            persist_directory=profile.vector_store.chroma_persist_dir,
        )
        return self.chroma.as_retriever()


class PineConeVectorStoreStrategy(VectorStoreStrategy):
    """
    Pinecone vector store strategy"""

    api_key: str = os.environ["PINECONE_KEY"]
    environment: str = profile.vector_store.pinecone_env

    def __init__(self, **kwargs):
        """
        Constructor"""
        super().__init__(**kwargs)
        pinecone.init(api_key=self.api_key, environment=self.environment)

    def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        """
        Get the retriever
        """

        pc = Pinecone.from_existing_index(
            index_name=self.index_name, embedding=get_embeddings()
        )
        return pc.as_retriever(search_kwargs={"k": k})

    async def write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        """
        Write to the store
        """

        try:
            pinecone.describe_index(self.index_name)
            if flush_index:
                pinecone.delete_index(self.index_name)
                pinecone.create_index(
                    self.index_name, profile.embedding.embedding_dimensions
                )
        except pinecone.exceptions.NotFoundException:
            pinecone.create_index(
                self.index_name, profile.embedding.embedding_dimensions
            )

        pc = Pinecone.from_documents(
            documents,
            get_embeddings(),
            index_name=self.index_name,
            api_key=self.api_key,
        )

        return pc.as_retriever()


class RedisVectorStoreStrategy(VectorStoreStrategy):
    """
    Redis vector store strategy
    """

    redis_url: str = profile.vector_store.redis_url

    def get_retriever(self, k, **kwargs) -> VectorStoreRetriever:
        return Redis.from_existing_index(
            redis_url=self.redis_url,
            index_name=self.index_name,
            embedding=get_embeddings(),
        ).as_retriever(k=k)

    async def write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        """
        Write to the store
        """

        if flush_index:
            Redis.drop_index(
                index_name=self.index_name,
                delete_documents=True,
                redis_url=self.redis_url,
            )

        rds = Redis.from_documents(
            documents,
            get_embeddings(),
            redis_url=self.redis_url,
            index_name=self.index_name,
        )
        return rds.as_retriever(search_type="similarity_limit")


def get_embeddings() -> Embeddings:
    """
    Get the embeddings
    """
    embeddings: Embeddings = None
    if profile.embedding.embeddings_function == "openai":
        embeddings = openai_embeddings
    else:
        embeddings = None
    return embeddings


STORE_STG = {
    "redis": RedisVectorStoreStrategy,
    "pinecone": PineConeVectorStoreStrategy,
    "chroma": ChromaVectorStoreStrategy,
}


# pylint: disable=unused-argument
def create_vector_store_strategy(**kwargs) -> VectorStoreStrategy:
    """
    Create a vector store strategy
    """
    return STORE_STG[profile.vector_store.vector_store_class].get_instance(
        embeddings=get_embeddings()
    )

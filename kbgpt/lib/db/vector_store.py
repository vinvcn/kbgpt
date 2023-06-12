import abc
import threading
from typing import List

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings

from langchain.vectorstores.base import VectorStoreRetriever
from redis import Redis as RedisType
from redis.lock import Lock

from config import profile
from kbgpt.lib.constants import REDIS_DOCUMENT_LOCK_NAME
from kbgpt.lib.db import check_lock
from kbgpt.lib.db.redis import MyRedis
from kbgpt.lib.openai import openai_embeddings

# from langchain.vectorstores import Chroma


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

    @abc.abstractmethod
    async def transctional_write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        """
        Transactional write to the store
        """


class RedisVectorStoreStrategy(VectorStoreStrategy):
    """
    Redis vector store strategy
    """

    redis_url: str = profile.vector_store.redis_url

    def __init__(self, embeddings: Embeddings) -> None:
        super().__init__(embeddings)
        self.client = RedisType.from_url(self.redis_url)
        self.redis_lock = Lock(
            self.client, REDIS_DOCUMENT_LOCK_NAME, blocking=False
        )

    def get_retriever(self, k, **kwargs) -> VectorStoreRetriever:
        return MyRedis.from_existing_index(
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
            MyRedis.drop_index(
                index_name=self.index_name,
                delete_documents=True,
                redis_url=self.redis_url,
            )
            MyRedis.drop_index(
                index_name=profile.cache.customer_service_cache_index,
                delete_documents=True,
                redis_url=self.redis_url,
            )

        rds = MyRedis.from_documents(
            documents,
            get_embeddings(),
            redis_url=self.redis_url,
            index_name=self.index_name,
        )
        return rds.as_retriever(search_type="similarity_limit")

    @check_lock
    async def transctional_write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        embeddings = get_embeddings()
        rds = MyRedis(
            self.redis_url,
            self.index_name,
            embedding_function=embeddings.embed_query,
            embeddings=get_embeddings(),
        )
        rds.write_lc_documents(documents, flush_index)
        return rds.as_retriever()


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
    # "pinecone": PineConeVectorStoreStrategy,
    # "chroma": ChromaVectorStoreStrategy,
}


# pylint: disable=unused-argument
def create_vector_store_strategy(**kwargs) -> VectorStoreStrategy:
    """
    Create a vector store strategy
    """
    return STORE_STG[profile.vector_store.vector_store_class].get_instance(
        embeddings=get_embeddings()
    )

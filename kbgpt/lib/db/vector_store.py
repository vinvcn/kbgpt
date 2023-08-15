import abc
from datetime import datetime
from enum import Enum
from typing import List
from uuid import uuid4

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStoreRetriever
from redis import Redis as RedisType
from redis.lock import Lock

from config import profile
from kbgpt.lib.constants import (
    CACHE_STATUS_KEY,
    INDEX_VERSION_KEY,
    REDIS_DOCUMENT_LOCK_NAME,
    CacheStatus,
)
from kbgpt.lib.db import IndexVersion, check_lock
from kbgpt.lib.db.redis import MyRedis, SetKeyToValue
from kbgpt.lib.openai import openai_embeddings

# from langchain.vectorstores import Chroma


class BusinessType(Enum):
    """storage class enum"""

    QA = "qa"
    PRODUCT_CATALOG = "product"


class VectorStoreStrategy(metaclass=abc.ABCMeta):
    """
    Abstract class for vector store strategies
    """

    def __init__(self, embeddings: Embeddings, index: str) -> None:
        super().__init__()
        self.embeddings = embeddings
        self.index_name = index

    @abc.abstractmethod
    def get_retriever(self, k: int, **kwargs) -> VectorStoreRetriever:
        """
        Get the retriever
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client = RedisType.from_url(self.redis_url)
        embeddings = get_embeddings()
        self.rds = MyRedis(
            self.redis_url,
            self.index_name,
            embedding_function=embeddings.embed_query,
            embeddings=get_embeddings(),
        )

    def get_retriever(self, k, **kwargs) -> VectorStoreRetriever:
        return MyRedis.from_existing_index(
            redis_url=self.redis_url,
            index_name=self.index_name,
            embedding=get_embeddings(),
        ).as_retriever(k=k, **kwargs)

    def get_write_to_store_pipeline(self, **kwargs):
        return self.rds.write_lc_pipeline(**kwargs)

    async def transctional_write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        ops = self.get_write_to_store_pipeline(
            documents=documents, flush_index=flush_index
        )
        self.rds.run_pipeline(ops)
        return self.rds.as_retriever()


class LockedRedisStrategy(RedisVectorStoreStrategy):
    """redis strategy with lock"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis_lock = Lock(self.client, REDIS_DOCUMENT_LOCK_NAME, blocking=False)

    def get_write_to_store_pipeline(self, **kwargs):
        ops = super().get_write_to_store_pipeline(**kwargs)
        ops.append(SetKeyToValue(key=CACHE_STATUS_KEY, value=CacheStatus.INVALID.value))
        # write the index version
        index_version = IndexVersion(
            uuid=str(uuid4()), timestamp=datetime.utcnow()
        ).json()
        ops.append(SetKeyToValue(key=INDEX_VERSION_KEY, value=index_version))
        return ops

    @check_lock
    async def transctional_write_to_store(
        self, documents: List[Document], flush_index=False, **kwargs
    ) -> VectorStoreRetriever:
        return await super().transctional_write_to_store(
            documents=documents, flush_index=flush_index, **kwargs
        )


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
    BusinessType.QA: LockedRedisStrategy(
        embeddings=get_embeddings(), index=profile.qa.redis_index
    ),
    BusinessType.PRODUCT_CATALOG: RedisVectorStoreStrategy(
        embeddings=get_embeddings(), index=profile.product_catalog.redis_index_name
    ),
}


# pylint: disable=unused-argument
def create_vector_store_strategy(business_type: str, **kwargs) -> VectorStoreStrategy:
    """
    Create a vector store strategy
    """
    return STORE_STG[BusinessType(business_type)]

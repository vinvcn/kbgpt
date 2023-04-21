import logging
from typing import List, Optional

import redis
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores.redis import Redis
from pydantic import BaseModel
from redis.client import Redis as RedisType
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from config import *

logger = logging.getLogger(__name__)

content_key: str = "content"
metadata_key: str = "metadata"
vector_key: str = "content_vector"


def _redis_prefix(index_name: str) -> str:
    """Redis key prefix for a given index."""
    return f"doc:{index_name}"


def _check_index_exists(client: RedisType, index_name: str) -> bool:
    """Check if Redis index exists."""
    try:
        client.ft(index_name).info()
    except:  # noqa: E722
        logger.info("Index does not exist")
        return False
    logger.info("Index already exists")
    return True


class RedisCacheStoreStrategy(BaseModel):
    """
    Redis cache store strategy
    """

    index_name: str = CUSTOMER_SERVICE_CACHE_INDEX
    embeddings: Optional[Embeddings]
    redis_client: Optional[RedisType]
    rds: Optional[Redis]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, embeddings: Embeddings, **kwargs) -> None:
        super().__init__(embeddings=embeddings, **kwargs)
        self.redis_client = redis.from_url(REDIS_URL)
        self.init_if_needed()
        self.rds = Redis.from_existing_index(
            redis_url=REDIS_URL,
            index_name=self.index_name,
            embedding=self.embeddings,
        )

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance"):
            cls.instance = super(RedisCacheStoreStrategy, cls).__new__(cls)
        return cls.instance

    def init_if_needed(self):
        """
        Initialize the index
        """
        if _check_index_exists(self.redis_client, self.index_name):
            return
        prefix = _redis_prefix(self.index_name)
        # Constants
        dim = int(EMBEDDING_DIMENSIONS)
        distance_metric = "COSINE"  # distance metric for the vectors (ex. COSINE, IP, L2)
        schema = (
            TextField(name=content_key),
            TextField(name=metadata_key),
            VectorField(
                vector_key,
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": dim,
                    "DISTANCE_METRIC": distance_metric,
                },
            ),
        )
        # Create Redis Index
        self.redis_client.ft(self.index_name).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH),
        )

    async def retrieve(self, query: str) -> Optional[dict]:
        """
        Retrieve from the store"""
        cached = self.rds.as_retriever(
            k=1, score_threshold=REDIS_CACHE_SIMILARITY_THRESHOLD, search_type="similarity_limit"
        ).get_relevant_documents(query=query)

        if len(cached) == 0:
            return None
        else:
            return {"question": cached[0].page_content, "answer": cached[0].metadata["answer"]}

    async def write_to_store(self, question: str, answer: str, **kwargs) -> VectorStoreRetriever:
        """
        Write to the store
        """
        doc = Document(
            page_content=question,
            metadata={"answer": answer},
        )
        self.rds.add_documents([doc])

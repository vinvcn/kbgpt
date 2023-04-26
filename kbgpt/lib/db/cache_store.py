"""
cache_store.py
"""
import logging
import threading
from typing import Optional

import redis
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores.redis import Redis
from redis.client import Redis as RedisType
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from config import profile

logger = logging.getLogger(__name__)


class RedisCacheStoreStrategy:
    """
    A singleton thread-safe Redis cache store strategy
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

    @staticmethod
    def _redis_prefix(index_name: str) -> str:
        """Redis key prefix for a given index."""
        return f"doc:{index_name}"

    @staticmethod
    def _check_index_exists(client: RedisType, index_name: str) -> bool:
        """Check if Redis index exists."""
        # pylint: disable=bare-except
        try:
            client.ft(index_name).info()
        except:  # noqa: E722
            logger.info("Index does not exist")
            return False
        logger.info("Index already exists")
        return True

    def __init__(self, embeddings: Embeddings) -> None:
        if hasattr(RedisCacheStoreStrategy, "instance"):
            raise ValueError(
                "An instantiation already exists!"
                " Use get_instance() instead."
            )
        else:
            super().__init__()
            self.index_name = profile.cache.customer_service_cache_index
            self.embeddings = embeddings
            self.redis_client = redis.from_url(profile.vector_store.redis_url)
            self.rds = Redis.from_existing_index(
                redis_url=profile.vector_store.redis_url,
                index_name=self.index_name,
                embedding=self.embeddings,
            )
            RedisCacheStoreStrategy.instance = self

    def init_if_needed(self):
        """
        Initialize the index
        """
        if self._check_index_exists(self.redis_client, self.index_name):
            return
        prefix = self._redis_prefix(self.index_name)
        # Constants
        dim = int(profile.embedding.embedding_dimensions)
        distance_metric = (
            "COSINE"  # distance metric for the vectors (ex. COSINE, IP, L2)
        )
        schema = (
            TextField(name="content"),
            TextField(name="metadata"),
            VectorField(
                "content_vector",
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
            definition=IndexDefinition(
                prefix=[prefix], index_type=IndexType.HASH
            ),
        )

    async def retrieve(self, query: str) -> Optional[dict]:
        """
        Retrieve from the store"""
        self.init_if_needed()
        docs_n_scores = self.rds.similarity_search_with_score(query=query, k=1)
        if len(docs_n_scores) == 0:
            logging.info("No results found in cache for query: %s", query)
            return None
        else:
            logging.info("similar doc retrieved:")
            logging.info("query: %s", query)
            logging.info("question: %s", docs_n_scores[0][0].page_content)
            logging.info("score %s", docs_n_scores[0][1])
            filtered = [
                (doc, score)
                for doc, score in docs_n_scores
                if score < profile.cache.redis_cache_similarity_threshold
            ]
            if len(filtered) == 0:
                logging.info(
                    "result score greater than threshold %s",
                    profile.cache.redis_cache_similarity_threshold,
                )
                return None
            else:
                logging.info(
                    "result socre %s, question %s less than threshold %s",
                    filtered[0][1],
                    filtered[0][0].page_content,
                    profile.cache.redis_cache_similarity_threshold,
                )
                return {
                    "question": filtered[0][0].page_content,
                    "answer": filtered[0][0].metadata["answer"],
                }

    async def write_to_store(
        self, question: str, answer: str, **kwargs
    ) -> VectorStoreRetriever:
        """
        Write to the store
        """
        self.init_if_needed()
        doc = Document(
            page_content=question,
            metadata={"answer": answer},
        )
        self.rds.add_documents([doc])

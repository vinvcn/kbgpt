"""
cache_store.py
"""
import functools
import logging
import pickle
import threading
import uuid
from os import getcwd, mkdir, path
from typing import List, Optional

import aioredis
import numpy as np
import redis
from langchain.docstore.document import Document
from langchain.vectorstores.base import VectorStoreRetriever
from redis.client import Redis as RedisType
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.exceptions import LockError
from redis.lock import Lock

from config import profile
from kbgpt.lib.db.redis import MyRedis
from kbgpt.lib.db.vector_store import get_embeddings
from kbgpt.svc.qa_services import QAagent

logger = logging.getLogger(__name__)


class CacheWarmingUpException(Exception):
    """
    cache warming up
    """

    pass


def check_lock(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.redis_lock.locked():
            raise CacheWarmingUpException()
        return await func(self, *args, **kwargs)

    return wrapper


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

    def __init__(self) -> None:
        if hasattr(RedisCacheStoreStrategy, "instance"):
            raise ValueError(
                "An instantiation already exists!"
                " Use get_instance() instead."
            )
        else:
            super().__init__()
            self.index_name = profile.cache.customer_service_cache_index
            self.embeddings = get_embeddings()
            self.redis_client = redis.from_url(profile.vector_store.redis_url)
            self.aredis = aioredis.from_url(profile.vector_store.redis_url)
            self.scan_match = f"{MyRedis._redis_prefix(self.index_name)}*"
            self._init_if_needed()
            self.fpath = None
            self.redis_lock = Lock(
                self.redis_client, "cache-index-lock", blocking=False
            )
            self.rds = MyRedis.from_existing_index(
                redis_url=profile.vector_store.redis_url,
                index_name=self.index_name,
                embedding=self.embeddings,
            )
            self.doc_rds = MyRedis.from_existing_index(
                redis_url=profile.vector_store.redis_url,
                index_name=profile.indexing.customer_service_index,
                embedding=self.embeddings,
            )
            RedisCacheStoreStrategy.instance = self

    def _init_if_needed(self):
        """
        Initialize the index
        """
        if self._check_index_exists(self.redis_client, self.index_name):
            return
        prefix = MyRedis._redis_prefix(self.index_name)
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

    @check_lock
    async def retrieve(self, query: str) -> Optional[dict]:
        """
        Retrieve from the store"""
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

    @check_lock
    async def write_to_store(
        self, question: str, answer: str, **kwargs
    ) -> VectorStoreRetriever:
        """
        Write to the store
        """
        doc = Document(
            page_content=question,
            metadata={"answer": answer},
        )
        self.rds.add_documents([doc])

    async def warmup_cache(self, fpath: str, batch_size: int = 10):
        """
        warm up the cache
        """

        try:
            with self.redis_lock:
                self.rds.drop_index(
                    self.index_name,
                    delete_documents=True,
                    redis_url=profile.vector_store.redis_url,
                )
                self._init_if_needed()
                k = profile.vector_store.vector_retrival_k
                end = False
                agent = QAagent.get_instance()
                with open(fpath, "rb") as fio:
                    while not end:
                        questions = []
                        documents = []
                        embeddings = []
                        try:
                            for _ in range(batch_size):
                                data = pickle.load(fio)
                                embd = np.frombuffer(
                                    data[1], dtype=np.float32
                                ).tolist()
                                docs = await self.doc_rds.asimilarity_search_by_vector(
                                    embd, k
                                )
                                questions.append(str(data[0], encoding="utf8"))
                                documents.append(docs)
                                embeddings.append(embd)

                        except EOFError:
                            end = True
                        answers = await agent.answer_question_in_batch(
                            questions, documents
                        )
                        metadatas = [{"answer": a} for a in answers]
                        await self.rds.write_all_to_store(
                            questions=questions,
                            metadatas=metadatas,
                            embeddings=embeddings,
                        )
        except LockError:
            raise CacheWarmingUpException()

    async def backup_cache(self, scan_size: int = 10000) -> str:
        """
        backup files
        """
        cursor = None
        rdir = path.join(getcwd(), ".redis")
        if not path.exists(rdir):
            mkdir(rdir)
        fpath = path.join(rdir, f"{str(uuid.uuid4())}.pkl")
        with open(fpath, "wb") as fio:
            while cursor != 0:
                cursor, keys = await self.aredis.scan(
                    cursor=cursor or 0, match=self.scan_match, count=scan_size
                )
                if keys:
                    for k in keys:
                        content, vector = await self.aredis.hmget(
                            k, "content", "content_vector"
                        )
                        fio.write(pickle.dumps((content, vector)))
            return fpath

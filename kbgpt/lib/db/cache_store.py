"""
Redis Cache Interation module
"""
import logging
import threading
import uuid
from typing import List, Optional

import numpy as np
import redis
from langchain.vectorstores.base import VectorStoreRetriever
from redis.client import Redis as RedisType
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.lock import Lock

from config import profile
from kbgpt.lib.constants import (
    CACHE_STATUS_KEY,
    INDEX_VERSION_KEY,
    REDIS_DOCUMENT_LOCK_NAME,
    CacheStatus,
)
from kbgpt.lib.db import (
    CacheMetadata,
    Document,
    IndexVersion,
    cache_status,
    ensure_lock,
)
from kbgpt.lib.db.redis import MyRedis, WriteToDoc
from kbgpt.lib.db.vector_store import get_embeddings
from kbgpt.svc.qa_services import QAagent

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
    def _check_index_exists(client: RedisType, index_name: str) -> bool:
        """Check if Redis index exists."""
        try:
            client.ft(index_name).info()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception(e)
            logger.error("fetching index information failed")
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
            # self.aredis = aioredis.from_url(profile.vector_store.redis_url)
            self.scan_match = f"{MyRedis._redis_prefix(self.index_name)}*"
            self._init_if_needed()
            self.fpath = None
            self.redis_lock = Lock(
                self.redis_client, REDIS_DOCUMENT_LOCK_NAME, blocking=False
            )
            self.rds: MyRedis = MyRedis.from_existing_index(
                redis_url=profile.vector_store.redis_url,
                index_name=self.index_name,
                embedding=self.embeddings,
            )
            self.doc_rds: MyRedis = MyRedis.from_existing_index(
                redis_url=profile.vector_store.redis_url,
                index_name=profile.indexing.customer_service_index,
                embedding=self.embeddings,
            )
            RedisCacheStoreStrategy.instance = self

    def is_cache_valid(self) -> bool:
        """
        Check if cache is valid
        """
        status = self.redis_client.get(CACHE_STATUS_KEY)
        if not status:
            return True
        status_str = status.decode("utf-8")
        return status_str == CacheStatus.VALID.value

    def get_index_version(self) -> IndexVersion:
        """
        get the version of the index
        """
        index_version = self.redis_client.get(INDEX_VERSION_KEY)

        if index_version is None:
            raise ValueError("Index version not found")
        index_version = index_version.decode("utf8")

        index_version = IndexVersion.parse_raw(index_version)

        return index_version

    def _redis_key(self, prefix: str) -> str:
        """Redis key schema for a given prefix."""
        return f"{prefix}:{uuid.uuid4().hex}"

    def _redis_prefix(self, index_name: str) -> str:
        """Redis key prefix for a given index."""
        return f"doc:{index_name}"

    def _init_if_needed(self):
        """
        Initialize the index
        """
        if self._check_index_exists(self.redis_client, self.index_name):
            return
        prefix = self._redis_prefix(self.index_name)

        schema = Document.to_redis_schema()
        # Create Redis Index
        self.redis_client.ft(self.index_name).create_index(
            fields=schema,
            definition=IndexDefinition(
                prefix=[prefix], index_type=IndexType.HASH
            ),
        )

    @cache_status
    async def retrieve(self, query: str) -> Optional[Document]:
        """
        Retrieve from the store"""

        embedding = self.embeddings.embed_query(query)

        docs_n_scores = self.rds.similarity_search_by_vector_with_score(
            vector=embedding, k=1
        )
        if len(docs_n_scores) == 0:
            logging.info("No results found in cache for query: %s", query)
            return None
        else:
            doc, score = docs_n_scores[0]
            # log the first record
            logging.info("similar doc retrieved:")
            logging.info("query: %s", query)
            logging.info("question: %s", doc.content)
            logging.info("score %s", score)
            threshold = profile.cache.redis_cache_similarity_threshold
            filtered = [
                (doc, score)
                for doc, score in docs_n_scores
                if score < threshold
            ]
            if len(filtered) == 0:
                logging.info(
                    "result score greater than threshold %s", threshold
                )
                return None
            else:
                logging.info(
                    "result socre %s, question %s less than threshold %s",
                    score,
                    doc.content,
                    threshold,
                )
                return doc

    @cache_status
    async def write_to_store(
        self, question: str, answer: str
    ) -> VectorStoreRetriever:
        """
        Write to the store
        """
        version = self.redis_client.get(INDEX_VERSION_KEY)
        doc = Document.from_one(
            question,
            CacheMetadata(version=version, answer=answer),
            self.embeddings.embed_query(question),
        )
        key = self._redis_key(self._redis_prefix(self.index_name))
        self.redis_client.hset(key, mapping=doc.dict())
        logging.info("writing key %s to cache", key)

    @ensure_lock
    async def refresh_cache(self, scan_size: int = 10000):
        """
        refresh the cache
        """
        index_version = self.get_index_version()
        logging.info(
            "refresh cache for index versioin: %s", index_version.json()
        )
        counter = 0
        index_version = index_version.uuid
        async for batch in self._read_batch(scan_size):
            batch = await self._filter_versioning(index_version, batch)
            if not batch:
                continue

            vectors = [
                np.frombuffer(v, dtype=np.float32).tolist()
                for _, _, v, _, in batch
            ]
            questions = [q for _, q, _, _, in batch]
            keys = [k for k, _, _, _, in batch]
            answers = await self._make_batch_http_req(
                questions, await self._fetch_docs(vectors)
            )

            documents = Document.from_lists(
                contents=questions,
                embeddings=vectors,
                metadatas=[
                    CacheMetadata(version=index_version, answer=a)
                    for a in answers
                ],
            )

            ops = [
                WriteToDoc(
                    keys=keys,
                    index_name=self.rds.index_name,
                    documents=documents,
                )
            ]

            self.rds.run_pipeline(ops)
            counter = counter + len(documents)

        self.redis_client.set(CACHE_STATUS_KEY, CacheStatus.VALID.value)
        logging.info(
            "refresh cache done total cache entries updated %d", counter
        )

    async def _read_batch(self, scan_size: int = 10000):
        cursor = None

        while cursor != 0:
            cursor, keys = self.redis_client.scan(
                cursor=cursor or 0, match=self.scan_match, count=scan_size
            )
            if keys:
                batch = []
                for k in keys:
                    content, vector, metadata = self.redis_client.hmget(
                        k,
                        Document._content_key,  # pylint: disable=protected-access
                        Document._vector_key,  # pylint: disable=protected-access
                        Document._metadata_key,  # pylint: disable=protected-access
                    )
                    obj = CacheMetadata.from_str(metadata)
                    batch.append((k, content, vector, obj.version))
                yield batch

    async def _filter_versioning(self, version: str, batch):
        return [
            (k, c, v, ver)
            for k, c, v, ver in batch
            if ver is None or ver != version
        ]

    async def _fetch_docs(self, vectors: List[List[float]]):
        documents = []
        for vector in vectors:
            docs = self.doc_rds.similarity_search_by_vector_n(
                vector, profile.vector_store.vector_retrival_k
            )
            documents.append(docs)
        return documents

    async def _make_batch_http_req(self, ques, docs):
        c_s = profile.cache.fresh_batch_size
        agent = QAagent.get_instance()
        answers = []
        for i in range(0, len(ques), c_s):
            ans = await agent.answer_question_in_batch(
                ques[i : i + c_s], docs[i : i + c_s]
            )
            answers.extend(ans)
        return answers

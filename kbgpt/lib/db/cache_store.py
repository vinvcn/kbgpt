"""
cache_store.py
"""
import json
import logging
import pickle
import threading
import uuid
from os import getcwd, mkdir, path
from typing import List, Mapping, Optional, Tuple

import aiofiles
import aioredis
import numpy as np
import redis
from aiofiles import tempfile
from aioredis.client import Redis as AioRedis
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores.redis import Redis
from redis.client import Redis as RedisType
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from config import profile
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

    def __init__(self) -> None:
        if hasattr(RedisCacheStoreStrategy, "instance"):
            raise ValueError(
                "An instantiation already exists!"
                " Use get_instance() instead."
            )
        else:
            super().__init__()
            self.index_name = profile.indexing.customer_service_index
            self.embeddings = get_embeddings()
            self.redis_client = redis.from_url(profile.vector_store.redis_url)
            self.aredis = aioredis.from_url(profile.vector_store.redis_url)
            self.scan_match = f"{self._redis_prefix(self.index_name)}*"
            self.init_if_needed()
            self.fpath = None
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
        doc = Document(
            page_content=question,
            metadata={"answer": answer},
        )
        self.rds.add_documents([doc])

    async def write_all_to_store(
        self, questions: List[str], answers: List[str], embeddings: List[bytes]
    ):
        pass

    async def similarity_search(self, embedding: bytes) -> List[Document]:
        k = profile.vector_store.vector_retrival_k
        return_fields = ["metadata", "content", "vector_score"]
        vector_field = "content_vector"
        hybrid_fields = "*"
        base_query = f"{hybrid_fields}=>[KNN {k} @{vector_field} $vector AS vector_score]"
        redis_query = (
            Query(base_query)
            .return_fields(*return_fields)
            .sort_by("vector_score")
            .paging(0, k)
            .dialect(2)
        )

        params_dict: Mapping[str, bytes] = {"vector": embedding}

        # perform vector search
        results = self.redis_client.ft(self.index_name).search(
            redis_query, params_dict
        )

        docs = [
            # (
            Document(
                page_content=result.content,
                metadata=json.loads(result.metadata),
            )
            #     float(result.vector_score),
            # )
            for result in results.docs
        ]

        return docs

    async def warmup(self):
        batch_size = 10
        end = False
        agent = QAagent.get_instance()
        with open(self.fpath, "rb") as fio:
            while not end:
                questions = []
                documents = []
                embeddings = []
                try:
                    for _ in range(batch_size):
                        data = pickle.load(fio)
                        # ( str, bytes )
                        docs = await self.similarity_search(data[1])
                        questions.append(data[0])
                        documents.append(docs)
                        embeddings.append(data[1])

                except EOFError:
                    end = True
                answers = await agent.answer_question_in_batch(
                    questions, documents
                )
                await self.write_all_to_store(
                    questions=questions, answers=answers, embeddings=embeddings
                )

    async def backup(self):
        """
        backup files
        """
        cursor = None
        batch_size = 10
        rdir = path.join(getcwd(), ".redis")
        if not path.exists(rdir):
            mkdir(rdir)
        self.fpath = path.join(rdir, f"{str(uuid.uuid4())}.pkl")
        with open(self.fpath, "wb") as fio:
            while cursor != 0:
                cursor, keys = await self.aredis.scan(
                    cursor=cursor or 0, match=self.scan_match, count=batch_size
                )
                if keys:
                    for k in keys:
                        content, vector = await self.aredis.hmget(
                            k, "content", "content_vector"
                        )
                        fio.write(pickle.dumps((content, vector)))
                        # pickle.dump((content, vector), fio)
                        # await fio.write(content)
                        # await fio.write(b"\n")
                        # await fio.write(vector)
                        # await fio.write(b"\n")

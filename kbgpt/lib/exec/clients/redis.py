import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, List, Mapping, Optional, Tuple

import numpy as np
import redis
from pydantic import BaseModel, Field
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from config import profile
from kbgpt.lib.exec.clients import ChatCompletion

logger = logging.getLogger(__name__)

INDEX_VERSION_KEY = "customer_service_index_version"


def check_index_exists(client: redis.client.Redis, index_name: str) -> bool:
    """Check if Redis index exists."""
    try:
        client.ft(index_name).info()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.warning(f"index {index_name} not exist")
        return False
    logging.info("Index already exists")
    return True


class VersionNotFound(Exception):
    """
    cache version not found exception
    """


class IndexVersion(BaseModel):
    """represent a cache version"""

    uuid: str
    timestamp: datetime


class CacheMetadata(BaseModel):
    """
    the metadata binding class
    """

    version: str = Field("")
    answer: str = Field("")
    source: str = Field("")

    @staticmethod
    def from_str(str_content):
        """create an object instance from json string"""
        obj = defaultdict(str, json.loads(str_content))
        return CacheMetadata(
            version=obj["version"],
            answer=obj["answer"],
            source=obj["source"],
        )


class CacheDocument(BaseModel):
    """
    cache document
    """

    content: str
    content_vector: bytes = Field(b"")
    metadata: CacheMetadata

    def dict(self, *args, **kwargs) -> Any:
        """
        override dict function to return an json metadata
        """
        obj = super().dict(exclude={"metadata"}, *args, **kwargs)
        obj["metadata"] = self.metadata.json()
        return obj

    @staticmethod
    def from_one(content: str, metadata: CacheMetadata, vector: List[float]):
        """create object from one representation"""
        return CacheDocument(
            content=content,
            content_vector=np.array(vector).astype(dtype=np.float32).tobytes(),
            metadata=metadata,
        )

    @classmethod
    def to_redis_schema(cls):
        """
        Maps to redis schema
        """
        dim = int(profile.embedding.embedding_dimensions)
        distance_metric = (
            "COSINE"  # distance metric for the vectors (ex. COSINE, IP, L2)
        )
        return (
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


class RedisStore:
    def __init__(self, redis_url) -> None:
        self.redis_client = redis.from_url(redis_url)
        self.embedding_client = ChatCompletion(model=profile.qa.embeddings_model)
        self.metadata_key = "metadata"
        self.vector_key = "content_vector"
        self.content_key = "content"

    def _redis_key(self, prefix: str) -> str:
        """Redis key schema for a given prefix."""
        return f"{prefix}:{uuid.uuid4().hex}"

    def _redis_prefix(self, index_name: str) -> str:
        """Redis key prefix for a given index."""
        return f"doc:{index_name}"

    def _init_if_needed(self, index_name):
        """
        Initialize the index
        """
        if check_index_exists(self.redis_client, index_name):
            return
        prefix = self._redis_prefix(index_name)

        schema = CacheDocument.to_redis_schema()
        # Create Redis Index
        self.redis_client.ft(index_name).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH),
        )

    def init_all_indexes(self, indexes):
        for index in indexes:
            self._init_if_needed(index)

    def remove_all_indexes(self, indexes):
        """
        remove all indexes if exists
        """
        for index in indexes:
            if check_index_exists(self.redis_client, index):
                self.drop_index(index)

    def reset_all_indexes(self, indexes):
        self.remove_all_indexes(indexes)
        self.init_all_indexes(indexes)

    async def _sim_search_wiz_score(
        self, index_name: str, vector: List[float], k: int = 4
    ) -> List[Tuple[CacheDocument, float]]:
        return_fields = [self.metadata_key, self.content_key, "vector_score"]
        vector_field = self.vector_key
        hybrid_fields = "*"
        base_query = (
            f"{hybrid_fields}=>[KNN {k} @{vector_field} $vector AS vector_score]"
        )
        redis_query = (
            Query(base_query)
            .return_fields(*return_fields)
            .sort_by("vector_score")
            .paging(0, k)
            .dialect(2)
        )
        params_dict: Mapping[str, str] = {
            "vector": np.array(vector)  # type: ignore
            .astype(dtype=np.float32)
            .tobytes()
        }

        # perform vector search
        results = self.redis_client.ft(index_name).search(redis_query, params_dict)

        docs = [
            (
                CacheDocument(
                    content=result.content,
                    metadata=CacheMetadata.from_str(result.metadata),
                ),
                float(result.vector_score),
            )
            for result in results.docs
        ]

        return docs

    def drop_index(self, index_name):
        """
        drop index
        """
        self.redis_client.ft(index_name=index_name).dropindex(delete_documents=True)

    def get_index_version(self) -> IndexVersion:
        """
        get the version of the index
        """
        index_version = self.redis_client.get(INDEX_VERSION_KEY)

        if index_version is None:
            raise VersionNotFound("Index version not found")
        index_version = index_version.decode("utf8")

        index_version = IndexVersion.parse_raw(index_version)

        return index_version

    async def retrieve_by_embed(
        self, embeddings: List[float], index_name: str
    ) -> Optional[CacheDocument]:
        self._init_if_needed(index_name)
        docs_n_scores = await self._sim_search_wiz_score(
            index_name=index_name,
            vector=embeddings,
        )
        if not docs_n_scores:
            return None
        else:
            threshold = profile.cache.redis_cache_similarity_threshold
            filtered = [
                (doc, score) for doc, score in docs_n_scores if score < threshold
            ]
            if not filtered:
                return None
            else:
                doc, _ = filtered[0]
                return doc

    async def retrieve(self, query: str, index_name: str) -> Optional[CacheDocument]:
        """
        get relavent document
        """

        embeddings = await self.embedding_client.embed(query)
        await self.retrieve_by_embed(embeddings=embeddings, index_name=index_name)

    async def write_to_store_wiz_embed(
        self, question: str, embeddings: List[float], answer: str, index_name: str
    ) -> bool:
        """write to store with embedding"""
        self._init_if_needed(index_name=index_name)
        version_number = ""
        try:
            index_version = self.get_index_version()
            version_number = index_version.uuid
        except VersionNotFound as e:
            logger.exception(e)
            logger.warning("index version not found")

        doc = CacheDocument.from_one(
            content=question,
            metadata=CacheMetadata(version=version_number, answer=answer),
            vector=embeddings,
        )
        key = self._redis_key(self._redis_prefix(index_name))
        self.redis_client.hset(key, mapping=doc.dict())

    async def write_to_store(self, question: str, answer: str, index_name: str) -> bool:
        """
        write it to store
        """
        embeddings = await self.embedding_client.embed(question)
        await self.write_to_store_wiz_embed(
            question=question,
            embeddings=embeddings,
            answer=answer,
            index_name=index_name,
        )


REDIS_CLIENT = RedisStore(profile.vector_store.redis_url)

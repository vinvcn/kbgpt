"""
this is the data storage module
"""
import functools
import json
from collections import defaultdict
from typing import Any, List

import numpy as np
from pydantic import BaseModel, Field
from redis.commands.search.field import TextField, VectorField

from config import profile


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


class Document(BaseModel):
    """
    A document represent a knowledge document
    """

    _content_key = "content"
    _vector_key = "content_vector"
    _metadata_key = "metadata"

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
        return Document(
            content=content,
            content_vector=np.array(vector).astype(dtype=np.float32).tobytes(),
            metadata=metadata,
        )

    @staticmethod
    def from_lists(
        contents: List[str],
        metadatas: List[CacheMetadata],
        embeddings: List[List[float]],
    ):
        """create list of objects from representations"""
        docs = []
        for c, m, e in zip(contents, metadatas, embeddings):
            docs.append(Document.from_one(content=c, vector=e, metadata=m))
        return docs

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


class CacheWarmingUpException(Exception):
    """
    cache warming up
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Failed to get redis lock, another thread might working"
            + " on warming up the index. Please try again later",
            *args
        )


class NotInExpectedStatusException(Exception):
    """
    cache invalid
    """


def cache_status(func):
    """
    check cache status is valid
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.is_cache_valid():
            raise NotInExpectedStatusException("Cache is not in Valid state")
        return await func(self, *args, **kwargs)

    return wrapper


def check_lock(func):
    """
    check lock
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.redis_lock.locked():
            raise CacheWarmingUpException()
        return await func(self, *args, **kwargs)

    return wrapper


def ensure_lock(func):
    """
    lock
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        with self.redis_lock:
            return await func(self, *args, **kwargs)

    return wrapper

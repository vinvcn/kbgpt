import json
import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Any, Callable, List, Mapping, Tuple
from uuid import uuid4

import numpy as np
from langchain.docstore.document import Document as LCDocument
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.redis import Redis, RedisVectorStoreRetriever
from pydantic import BaseModel
from redis.client import Pipeline
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from kbgpt.lib.constants import CACHE_STATUS_KEY, INDEX_VERSION_KEY, CacheStatus
from kbgpt.lib.db import CacheMetadata, Document, IndexVersion
from kbgpt.lib.db.utils import check_index_exists


class RedisOps(BaseModel, metaclass=ABCMeta):
    """
    Represent an abstract redis operation
    """

    @abstractmethod
    def __call__(self, pipeline: Pipeline, *args: Any, **kwds: Any) -> Any:
        pass


class CreateIndex(RedisOps):
    """represent a index creation"""

    name: str
    redis_schema: Tuple

    def __call__(self, pipeline: Pipeline, *args: Any, **kwds: Any) -> Any:
        super().__call__(pipeline, *args, **kwds)

        prefix = f"doc:{self.name}"
        return pipeline.ft(self.name).create_index(
            fields=self.redis_schema,
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH),
        )


class FlushIndex(RedisOps):
    """
    Represent a search index
    """

    name: str
    redis_schema: Tuple

    def __call__(self, pipeline: Pipeline, *args: Any, **kwds: Any) -> Pipeline:
        super().__call__(pipeline, *args, **kwds)
        pipeline.ft(self.name).dropindex(delete_documents=True)
        prefix = f"doc:{self.name}"
        return pipeline.ft(self.name).create_index(
            fields=self.redis_schema,
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH),
        )


class WriteToDoc(RedisOps):
    """
    write to langchain document
    """

    index_name: str
    keys: List[str] = list()
    documents: List[Any]

    def __call__(self, pipeline: Pipeline, *args: Any, **kwds: Any) -> Any:
        super().__call__(pipeline, *args, **kwds)
        prefix = f"doc:{self.index_name}"
        ids = []
        for i, doc in enumerate(self.documents):
            key = None
            if self.keys:
                key = self.keys[i]
            else:
                key = f"{prefix}:{uuid.uuid4().hex}"
            pipeline.hset(
                key,
                mapping=doc.dict(),
            )
            ids.append(key)
        return ids


class SetKeyToValue(RedisOps):
    """
    set a key to given value
    """

    key: str
    value: str

    def __call__(self, pipeline: Pipeline, *args: Any, **kwds: Any) -> Any:
        super().__call__(pipeline, *args, **kwds)
        pipeline.set(self.key, self.value)


class MyRedisVectorRetiever(RedisVectorStoreRetriever):
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)


class MyRedis(Redis):
    """
    Redis implementation of the vector store.
    """

    def __init__(
        self,
        redis_url: str,
        index_name: str,
        embedding_function: Callable,
        content_key: str = "content",
        metadata_key: str = "metadata",
        vector_key: str = "content_vector",
        *args: Any,
        **kwargs: Any,
    ):
        self.embeddings: Embeddings = (
            kwargs.pop("embeddings") if "embeddings" in kwargs else None
        )
        super().__init__(
            redis_url,
            index_name,
            embedding_function,
            content_key,
            metadata_key,
            vector_key,
            *args,
            **kwargs,
        )

    @staticmethod
    def _redis_key(prefix: str) -> str:
        """Redis key schema for a given prefix."""
        return f"{prefix}:{uuid.uuid4().hex}"

    @staticmethod
    def _redis_prefix(index_name: str) -> str:
        """Redis key prefix for a given index."""
        return f"doc:{index_name}"

    def run_pipeline(self, ops: List[RedisOps]):
        """run for the given pipeline"""
        pipeline = self.client.pipeline()
        for op in ops:
            op(pipeline)
        pipeline.execute()

    def as_retriever(self, **kwargs: Any) -> MyRedisVectorRetiever:
        return MyRedisVectorRetiever(vectorstore=self, **kwargs)

    def write_lc_pipeline(
        self,
        documents: List[LCDocument],
        flush_index: bool = False,
        **kwargs: Any,
    ) -> List[RedisOps]:
        """
        Create a new Redis index from a list of documents.
        """

        ops = []
        index_exist = check_index_exists(self.client, self.index_name)
        if not index_exist:
            # create new index
            ops.append(
                CreateIndex(
                    name=self.index_name, redis_schema=Document.to_redis_schema()
                )
            )
        elif flush_index:
            # flush existing index
            ops.append(
                FlushIndex(
                    name=self.index_name,
                    redis_schema=Document.to_redis_schema(),
                )
            )
        texts = [d.page_content for d in documents]
        metadatas = [d.metadata if d.metadata else {} for d in documents]
        embeddings = self.embeddings.embed_documents(texts)

        documents = Document.from_lists(
            contents=texts, metadatas=metadatas, embeddings=embeddings
        )

        ops.append(WriteToDoc(index_name=self.index_name, documents=documents))
        return ops

    async def write_cache_documents(
        self,
        questions: List[str],
        metadatas: List[dict],
        embeddings: List[List[float]],
    ):
        """Add all data to an existing index."""
        prefix = self._redis_prefix(self.index_name)
        ids = []

        pipeline = self.client.pipeline(transaction=False)
        for q, m, e in zip(questions, metadatas, embeddings):
            key = self._redis_key(prefix)

            pipeline.hset(
                key,
                mapping={
                    "content": q,
                    "content_vector": np.array(e)  # type: ignore
                    .astype(dtype=np.float32)
                    .tobytes(),
                    "metadata": json.dumps(m),
                },
            )
            ids.append(key)
        pipeline.execute()
        return ids

    def similarity_search_by_vector_n(
        self, vector: List[float], k: int = 4
    ) -> List[Document]:
        """similarity search"""
        docs_and_scores = self.similarity_search_by_vector_with_score(
            vector=vector, k=k
        )
        return [doc for doc, _ in docs_and_scores]

    def similarity_search_by_vector_with_score(
        self, vector: List[float], k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        similarity search, returns document and score
        """
        # Prepare the Query
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
        results = self.client.ft(self.index_name).search(redis_query, params_dict)

        docs = [
            (
                Document(
                    content=result.content,
                    metadata=CacheMetadata.from_str(result.metadata),
                ),
                float(result.vector_score),
            )
            for result in results.docs
        ]

        return docs

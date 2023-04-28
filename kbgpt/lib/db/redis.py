import json
import uuid
from typing import Any, List, Mapping, Tuple

import numpy as np
from langchain.docstore.document import Document
from langchain.vectorstores.redis import Redis
from redis.commands.search.query import Query


class MyRedis(Redis):
    @staticmethod
    def _redis_key(prefix: str) -> str:
        """Redis key schema for a given prefix."""
        return f"{prefix}:{uuid.uuid4().hex}"

    @staticmethod
    def _redis_prefix(index_name: str) -> str:
        """Redis key prefix for a given index."""
        return f"doc:{index_name}"

    async def write_all_to_store(
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

    def similarity_search_by_vector(
        self, embedding: List[float], k: int = 4, **kwargs: Any
    ) -> List[Document]:
        """similarity search"""
        docs_and_scores = self.similarity_search_by_vector_with_score(
            embedding=embedding, k=k
        )
        return [doc for doc, _ in docs_and_scores]

    def similarity_search_by_vector_with_score(
        self, embedding: List[float], k: int = 4, **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        # Prepare the Query
        return_fields = [self.metadata_key, self.content_key, "vector_score"]
        vector_field = self.vector_key
        hybrid_fields = "*"
        base_query = f"{hybrid_fields}=>[KNN {k} @{vector_field} $vector AS vector_score]"
        redis_query = (
            Query(base_query)
            .return_fields(*return_fields)
            .sort_by("vector_score")
            .paging(0, k)
            .dialect(2)
        )
        params_dict: Mapping[str, str] = {
            "vector": np.array(embedding)  # type: ignore
            .astype(dtype=np.float32)
            .tobytes()
        }

        # perform vector search
        results = self.client.ft(self.index_name).search(
            redis_query, params_dict
        )

        docs = [
            (
                Document(
                    page_content=result.content,
                    metadata=json.loads(result.metadata),
                ),
                float(result.vector_score),
            )
            for result in results.docs
        ]

        return docs

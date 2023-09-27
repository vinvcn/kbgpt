from typing import Any, Dict, List

from config import profile
from kbgpt.lib.db.redis import MyRedis
from kbgpt.lib.db.vector_store import get_embeddings
from kbgpt.lib.exec.engines.configs.models import SimilaritySearchMod

from .engine import Engine


class SimilaritySearch(Engine):
    """search redis index for given embedding"""

    def __init__(self, config: SimilaritySearchMod) -> None:
        super().__init__(config)
        embedding_func = get_embeddings()
        self.redis: MyRedis = MyRedis.from_existing_index(
            embedding_func, config.index, redis_url=profile.vector_store.redis_url
        )

    async def agenerate(
        self, *, embedding: List[float], invoke_id=None, envs=None, **kwargs
    ) -> Dict[str, Any]:
        matchings = self.redis.similarity_search_by_vector_with_score(
            embedding, self.config.k
        )
        # map it to string
        # limited = "\n".join(
        #     [
        #         m.content
        #         for m, s in matchings
        #         if s < (self.config.min_threshold if self.config.min_threshold else 1)
        #     ]
        # )
        limited = [
            (m.dict(), s)
            for m, s in matchings
            if s < (self.config.min_threshold if self.config.min_threshold else 1)
        ]
        return {"result": limited}

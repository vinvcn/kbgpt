import numpy as np

from config import PROF_MGR
from kbgpt.lib.db import Document
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.redis import WriteToDoc


class RedisCacheCopier():
    """
    redis copier
    """

    def __init__(self) -> None:
        self.src:RedisCacheStoreStrategy = RedisCacheStoreStrategy(PROF_MGR.primary_profile)
        self.dest:RedisCacheStoreStrategy = RedisCacheStoreStrategy(PROF_MGR.secondary_profile)


    async def copy_cache(self, scan_size: int = 10000):
        """ copy cache between redis """

        async for batch in self.src.read_cache_batch(scan_size):

            questions = [q for _, q, _, _, in batch]
            keys = [k for k, _, _, _, in batch]
            vectors = [
                np.frombuffer(v, dtype=np.float32).tolist() for _, _, v, _, in batch
            ]
            meta = [obj for _, _, _, obj in batch]

            documents = Document.from_lists(
                contents=questions,
                embeddings=vectors,
                metadatas=meta,
            )

            ops = [WriteToDoc(
                keys=keys,
                index_name=self.dest.rds.index_name,
                documents=documents,
            )]

            self.dest.rds.run_pipeline(ops)

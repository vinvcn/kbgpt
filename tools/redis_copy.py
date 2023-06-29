import asyncio

from kbgpt.lib.db.cache_maintainer import RedisCacheCopier

copier = RedisCacheCopier()
asyncio.run(copier.copy_cache())

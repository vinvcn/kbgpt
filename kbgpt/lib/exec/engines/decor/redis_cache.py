"""
pass
"""


import functools

from config import profile
from kbgpt.lib.exec.clients.redis import REDIS_CLIENT
from kbgpt.lib.exec.engines.configs.models import CacheMod, EngineMod


def rediscache(func):
    @functools.wraps(func)
    async def wrapper_function(self, *args, **kwargs):
        """decorate it"""
        assert "config" in self.__dict__ and isinstance(self.config, EngineMod)
        config: CacheMod = (
            self.config.cache if "cache" in self.config.__dict__ else None
        )

        use_cache = config and config.enabled and profile.cache.global_enabled

        cache_doc = None

        if use_cache:
            cache_index = config.index_name
            cache_doc = await REDIS_CLIENT.retrieve_by_embed(
                index_name=cache_index,
                embeddings=kwargs["embedding"],
            )

        if cache_doc:
            result = {"result": cache_doc.metadata.answer}
            # usage = "{}"
        else:
            result = await func(self, *args, **kwargs)

            if use_cache:
                await REDIS_CLIENT.write_to_store_wiz_embed(
                    question=kwargs[self.config.cache.query_key],
                    answer=result["result"],
                    index_name=cache_index,
                    embeddings=kwargs["embedding"],
                )

        return result

    return wrapper_function

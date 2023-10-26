import json
from typing import Any, Dict, List, Tuple

import redis
from async_lru import alru_cache

from config import profile
from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.db import Document
from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.engines.configs.models import EngineMod, RecomOutTransMod


class QAOutput(Engine):
    async def agenerate(
        self, *, invoke_id=None, answer: str, envs=None, **kwargs
    ) -> Dict[str, Any]:
        """generate the template"""
        result = {
            "success": True,
            "answer": answer,
        }
        if self.config.stream:
            assert "callbacks" in kwargs
            for clbk in kwargs["callbacks"]:
                clbk: StreamingAsyncHandler = clbk
                await clbk.send(f"data: {json.dumps(result)}\n")
        return {"result": result}


class RecommOutTransform(Engine):
    def __init__(self, mod: EngineMod) -> None:
        super().__init__(mod=mod)
        self.redis_client = redis.from_url(profile.vector_store.redis_url)

    # @alru_cache(maxsize=10)
    async def load_products(self):
        keys = self.redis_client.keys(
            f"doc:{profile.product_catalog.redis_index_name}:*"
        )
        raw_content = [
            self.redis_client.hmget(k, Document._content_key)[0].decode("utf8")
            for k in keys
        ]

        products = [json.loads(str(raw_rst)) for raw_rst in raw_content]
        return products

    async def agenerate(
        self,
        *,
        recomm: str,
        invoke_id=None,
        envs=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """generate the template"""
        ids = [spl.strip() for spl in recomm.split(",")]
        config: RecomOutTransMod = self.config
        ids = ids[: config.max_output]
        all_product = await self.load_products()
        objs_m = {o["id"]: o for o in all_product}
        result = []
        for i in ids:
            result.append(objs_m[i])
        return {"result": result}


class RecommOutput(Engine):
    async def agenerate(
        self, *, products: List[Dict], hook: str, invoke_id=None, envs=None, **kwargs
    ) -> Dict[str, Any]:
        """generate the template"""
        result = {
            "success": True,
            "answer": hook,
            "intents": [{"id": int(prod["id"])} for prod in products],
        }
        if self.config.stream:
            assert "callbacks" in kwargs
            for clbk in kwargs["callbacks"]:
                clbk: StreamingAsyncHandler = clbk
                await clbk.send(f"data: {json.dumps(result)}\n")
        return {"result": result}


class FunctionOutput(Engine):
    """function output"""

    async def agenerate(
        self, *, answer, recommend, invoke_id=None, envs=None, **kwargs
    ) -> Dict[str, Any]:
        result = {
            "success": True,
            "answer": answer,
            "recommend": recommend,
        }
        if self.config.stream:
            assert "callbacks" in kwargs
            for clbk in kwargs["callbacks"]:
                clbk: StreamingAsyncHandler = clbk
                await clbk.send(f"data: {json.dumps(result)}\n")
        return {"result": result}

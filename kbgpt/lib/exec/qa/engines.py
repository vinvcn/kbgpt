import json
from typing import Any, Dict, List, Tuple

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.db import Document
from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.engines.configs.models import RecomOutTransMod


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
                await clbk.send(f"data: {json.dumps(result)}")
        return {"result": result}


class RecommOutTransform(Engine):
    async def agenerate(
        self,
        *,
        recomm: str,
        products: List[Tuple[Document, float]],
        invoke_id=None,
        envs=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """generate the template"""
        ids = [spl.strip() for spl in recomm.split(",")]
        config: RecomOutTransMod = self.config
        ids = ids[: config.max_output]
        objs = [json.loads(d["content"]) for d, _ in products]
        objs_m = {o["id"]: o for o in objs}
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
                await clbk.send(f"data: {json.dumps(result)}")
        return {"result": result}

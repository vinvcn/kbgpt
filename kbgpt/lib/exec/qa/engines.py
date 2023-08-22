import json
from typing import Any, Dict, List, Tuple

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.db import Document
from kbgpt.lib.exec.engines import Engine


class QAOutput(Engine):
    async def agenerate(self, answer: str, **kwargs) -> Dict[str, Any]:
        """generate the template"""
        result = {
            "success": True,
            "answer": answer,
        }
        if self.config.stream:
            assert "callbacks" in kwargs
            for clbk in kwargs["callbacks"]:
                clbk: StreamingAsyncHandler = clbk
                await clbk.send(json.dumps(result))
        return {"result": result}


class RecommOutTransform(Engine):
    async def agenerate(
        self, recomm: str, products: List[Tuple[Document, float]], **kwargs
    ) -> Dict[str, Any]:
        """generate the template"""
        ids = [spl.strip() for spl in recomm.split(",")]
        ids = ids[:4]
        objs = [json.loads(d["content"]) for d, _ in products]
        objs_m = {o["id"]: o for o in objs}
        result = []
        for i in ids:
            result.append(objs_m[i])
        return {"result": result}


class RecommOutput(Engine):
    async def agenerate(
        self, products: List[Dict], hook: str, **kwargs
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
                await clbk.send(json.dumps(result))
        return {"result": result}

import logging
from typing import Any, Dict

from kbgpt.lib.exec.engines.configs.models import EmbedMod
from kbgpt.lib.llm.openai import OpenAI

from .engine import Engine


class Embed(Engine):
    """engine that calculates embeddings"""

    def __init__(self, config: EmbedMod) -> None:
        super().__init__()
        self.config = config
        self.openai = OpenAI()

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        assert all([k in kwargs for k in self.config.key_and_labels])
        content = "\n".join(
            f"{l}:\n {kwargs[k]}" if l else kwargs[k]
            for k, l in self.config.key_and_labels.items()
        )
        logging.debug("getting embeddings for content of length %d", len(content))
        embedding = await self.openai.embed(content)
        return {"result": embedding}

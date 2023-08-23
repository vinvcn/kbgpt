from typing import Any, Dict

from kbgpt.lib.exec.engines.configs.models import SimpleMod
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.llm.openai import Message, OpenAI

from .engine import Engine


class SimpleEngine(Engine):
    """clasify engine"""

    def __init__(self, config: SimpleMod):
        super().__init__(config)
        self.tmp_repo = TemplateFactory().create()
        self.openai = OpenAI()

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        assert all(
            [k in kwargs for k in self.config.keys_in]
        ), f"keys required but not in params {set(self.config.keys_in) - set(kwargs.keys())}"

        rendered = await self.tmp_repo.render(name=self.config.name, **kwargs)
        completion = await self.openai.chat_completion(
            self.config.models, tuple([Message(role="system", content=rendered)])
        )
        completion.prompt = rendered
        return {"result": completion.content}

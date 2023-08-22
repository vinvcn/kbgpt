import json
from typing import Any, Dict, List

from jinja2 import Environment

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.exec.engines.configs.models import JinjaMod
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.lib.templates.rendering.models import Jinja2RedisLoader

from .engine import Engine


class Jinja(Engine):
    def __init__(self, config: JinjaMod):
        super().__init__(config)
        self.tmp_repo = TemplateFactory().create()
        self.jinja_env = Environment(
            trim_blocks=True, lstrip_blocks=True, loader=Jinja2RedisLoader()
        )
        self.openai = OpenAI()

        def split_lists_str(lst_str: List[str]):
            return "\n---\n".join(lst_str)

        def json_loads(json_str: str):
            return json.loads(json_str)

        self.jinja_env.filters["split_lists_str"] = split_lists_str
        self.jinja_env.filters["json_loads"] = json_loads

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        assert all(
            [k in kwargs for k in self.config.keys_in]
        ), f"keys required but not in params {set(self.config.keys_in) - set(kwargs.keys())}"

        template = self.jinja_env.get_template(self.config.name)
        rendered = template.render(**kwargs)
        if not self.config.stream:
            completion = await self.openai.chat_completion(
                self.config.models[0], tuple([Message(role="system", content=rendered)])
            )

            return {"result": completion.content}
        else:
            assert "callbacks" in kwargs
            request = await self.openai.chat_completion(
                self.config.models[0],
                tuple([Message(role="system", content=rendered)]),
                stream=True,
            )
            buffer = ""
            callbacks: List[StreamingAsyncHandler] = kwargs["callbacks"]
            async for stream_resp in request:
                token = stream_resp["choices"][0]["delta"].get("content", "")
                buffer += token
                for cb in callbacks:
                    await cb.on_llm_new_token(token)
            return {"result": buffer}

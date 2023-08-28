import json
from time import perf_counter
from typing import Any, Dict, List

from jinja2 import Environment

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.mysql.jinja_engine_record import JinjaTemplateRecord
from kbgpt.lib.exec.engines.configs.models import JinjaMod, PersistLevel
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.lib.templates.rendering.models import Jinja2RedisLoader

from .engine import Engine


class Jinja(Engine):
    def __init__(self, config: JinjaMod):
        super().__init__(config)
        self.tmp_repo = TemplateFactory().create()
        self.jinja_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            auto_reload=True,
            loader=Jinja2RedisLoader(),
        )
        self.openai = OpenAI()

        def split_lists_str(lst_str: List[str]):
            return "\n---\n".join(lst_str)

        def json_loads(json_str: str):
            return json.loads(json_str)

        self.jinja_env.filters["split_lists_str"] = split_lists_str
        self.jinja_env.filters["json_loads"] = json_loads

    async def _persist_content(self, envs: Dict[str, Any], **kwargs):
        if self.config.persist_level != PersistLevel.NONE.value:
            res_mgr: ResourceMgr = envs["res"]
            emitter: MySqlEmitter = res_mgr.get(MySqlEmitter.__name__)
            record = JinjaTemplateRecord(**kwargs)
            await emitter.aemit([record])

    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        assert all(
            [k in kwargs for k in self.config.keys_in]
        ), f"keys required but not in params {set(self.config.keys_in) - set(kwargs.keys())}"

        start_time = perf_counter()
        template = self.jinja_env.get_template(self.config.name)
        rendered = template.render(**kwargs)

        result = ""
        usage = None
        if not self.config.stream:
            completion = await self.openai.chat_completion(
                self.config.models,
                tuple([Message(role="system", content=rendered)]),
                temperature=self.config.temperature,
            )

            result, usage = completion.content, completion.usage.json()
        else:
            assert "callbacks" in kwargs
            request = await self.openai.chat_completion(
                self.config.models,
                tuple([Message(role="system", content=rendered)]),
                stream=True,
                temperature=self.config.temperature,
            )
            buffer = ""
            callbacks: List[StreamingAsyncHandler] = kwargs["callbacks"]
            async for stream_resp in request:
                token = stream_resp["choices"][0]["delta"].get("content", "")
                buffer += token
                for cb in callbacks:
                    await cb.on_llm_new_token(token)

            result, usage = buffer, "{}"

        await self._persist_content(
            envs=envs,
            invoke_id=invoke_id,
            node_id=self.config.name,
            prompt=rendered,
            result=result,
            seconds_spent=perf_counter() - start_time,
            usage=usage,
        )

        return {"result": result}

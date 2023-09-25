import json
from time import perf_counter
from typing import Any, Dict, List

from jinja2 import Environment

from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.db.mysql.jinja_engine_record import JinjaTemplateRecord
from kbgpt.lib.exec.clients import CLIENT
from kbgpt.lib.exec.clients.redis import REDIS_CLIENT
from kbgpt.lib.exec.engines.configs.models import ClientStyle, JinjaMod, PersistLevel
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter
from kbgpt.lib.templates.rendering.models import Jinja2RedisLoader

from .engine import Engine


class JinjaClientProvider:
    async def request(self):
        pass

    async def stream_request(self):
        pass


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

    async def _get_from_db_if_has(
        self, envs: Dict[str, Any], **kwargs
    ) -> JinjaTemplateRecord:
        if self.config.persist_level != PersistLevel.NONE.value:
            res_mgr: ResourceMgr = envs["res"]
            crud: Crud = res_mgr.get(Crud.__name__)
            return crud.get_first_by(
                JinjaTemplateRecord, filter_params={**kwargs}, order_col="timestamp"
            )

    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        assert all(
            [k in kwargs for k in self.config.keys_in]
        ), f"keys required but not in params {set(self.config.keys_in) - set(kwargs.keys())}"

        start_time = perf_counter()
        template = self.jinja_env.get_template(self.config.name)
        rendered = template.render(**kwargs)
        load_from_db = await self._get_from_db_if_has(
            envs, invoke_id=invoke_id, node_id=self.config.name
        )

        result = ""
        usage = None
        if load_from_db and load_from_db.prompt == rendered:
            result, usage = load_from_db.result, load_from_db.usage
        else:
            cache_doc = None
            if self.config.cache and self.config.cache.enabled:
                cache_index = self.config.cache.index_name
                cache_doc = await REDIS_CLIENT.retrieve(
                    query=kwargs[self.config.cache.query_key], index_name=cache_index
                )

            if cache_doc:
                result = cache_doc.metadata.answer
                usage = "{}"
            else:
                result, usage = await self.make_request(kwargs, rendered)
                if self.config.cache and self.config.cache.enabled:
                    await REDIS_CLIENT.write_to_store(
                        question=kwargs[self.config.cache.query_key],
                        answer=result,
                        index_name=cache_index,
                    )

        if not load_from_db:
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

    async def make_request(self, kwargs, rendered):
        if self.config.client_style == ClientStyle.ROUNDROBIN.value:
            completion = await CLIENT.chat_completion(
                messages=[Message(role="system", content=rendered)],
                stream=self.config.stream,
                callbacks=kwargs.get("callbacks", None),
                temperature=self.config.temperature,
            )
            result, usage = completion.content, completion.usage.json()
        elif self.config.client_style == ClientStyle.NATIVE.value:
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
        else:
            raise ValueError(f"no such client style '{self.config.client_style}")
        return result, usage

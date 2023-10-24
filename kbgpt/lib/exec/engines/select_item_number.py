import enum
from time import perf_counter
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.mysql.jinja_engine_record import JinjaTemplateRecord
from kbgpt.lib.exec.clients import CLIENT
from kbgpt.lib.exec.clients.redis import REDIS_CLIENT
from kbgpt.lib.exec.engines.configs.models import (
    ClassificationMod,
    ClientStyle,
    PersistLevel,
)
from kbgpt.lib.exec.engines.decor.redis_cache import rediscache
from kbgpt.lib.exec.engines.engine import Engine
from kbgpt.lib.exec.template_factory import JINJA_ENV, TemplateFactory
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter


class ClassificationEngine(Engine):
    """select item number"""

    TEMPLATE_NAME = "classification.classification_with_context_and_question"

    def __init__(self, mod: ClassificationMod) -> None:
        super().__init__(mod)
        self.tmp_repo = TemplateFactory().create()
        self.jinja_env = JINJA_ENV
        self.openai = OpenAI()
        # if mod.cache.clear_on_init:
        #     REDIS_CLIENT.remove_all_indexes([mod.cache.index_name])

    async def _persist_content(self, envs: Dict[str, Any], **kwargs):
        res_mgr: ResourceMgr = envs["res"]
        emitter: MySqlEmitter = res_mgr.get(MySqlEmitter.__name__)
        record = JinjaTemplateRecord(**kwargs)
        await emitter.aemit([record])

    @rediscache
    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        """generate the template"""
        config: ClassificationMod = self.config
        start_time = perf_counter()
        context = ""
        if "context" in kwargs:
            context = kwargs["context"]

        assert "question" in kwargs

        params = {
            "context": context,
            "question": kwargs["question"],
            "amc": kwargs["amc"],
            "product": kwargs["product"],
            "mapping": config.mapping,
        }

        template = self.jinja_env.get_template(self.TEMPLATE_NAME)
        rendered = template.render(**params)
        completion = await self.make_request(rendered)

        result, usage = completion.content, completion.usage.json()

        await self._persist_content(
            envs=envs,
            invoke_id=invoke_id,
            node_id=self.TEMPLATE_NAME,
            prompt=rendered,
            result=result,
            seconds_spent=perf_counter() - start_time,
            usage=usage,
        )

        return {"result": result}

    async def make_request(self, rendered):
        config: ClassificationMod = self.config
        few_shot_msg = [
            Message(role="system", content=rendered),
        ]
        completion = None
        if self.config.client_style == ClientStyle.ROUNDROBIN.value:
            completion = await CLIENT.chat_completion(
                messages=few_shot_msg,
                stream=False,
                temperature=config.temperature,
            )
        else:
            completion = await self.openai.chat_completion(
                self.config.model,
                tuple(few_shot_msg),
                temperature=config.temperature,
            )

        return completion

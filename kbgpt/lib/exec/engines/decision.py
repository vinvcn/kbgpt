import abc
import logging
import re
from time import perf_counter
from typing import Any, Dict

from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.mysql.jinja_engine_record import JinjaTemplateRecord
from kbgpt.lib.exec.clients import CLIENT
from kbgpt.lib.exec.engines.configs.models import (
    ClassificationMod,
    ClientStyle,
    DecisionMod,
    DecisionTreeMod,
    EngineMod,
)
from kbgpt.lib.exec.engines.decor.redis_cache import rediscache
from kbgpt.lib.exec.engines.engine import Engine
from kbgpt.lib.exec.template_factory import JINJA_ENV, TemplateFactory
from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.lib.logging.mysql_emitter import MySqlEmitter


class DecisionEngine(Engine):
    """decision engine"""

    @property
    def template_name(self):
        """template name"""
        return ""

    @property
    def node_id(self):
        """node name"""
        return ""

    def __init__(self, mod: DecisionMod) -> None:
        super().__init__(mod)
        self.tmp_repo = TemplateFactory().create()
        self.jinja_env = JINJA_ENV
        self.openai = OpenAI()

    async def _persist_content(self, envs: Dict[str, Any], **kwargs):
        res_mgr: ResourceMgr = envs["res"]
        emitter: MySqlEmitter = res_mgr.get(MySqlEmitter.__name__)
        record = JinjaTemplateRecord(**kwargs)
        await emitter.aemit([record])

    @abc.abstractmethod
    async def agen_helper(self, *, invoke_id=None, envs=None, **kwargs):
        """render prompt"""

    async def extract_result(self, content):
        """extract result"""
        config: DecisionMod = self.config
        if config.rst_regex:
            matched = re.match(config.rst_regex, content)
            if matched:
                return matched.group()
            else:
                return None

    async def make_request(self, rendered):
        """make request"""
        config: DecisionMod = self.config
        few_shot_msg = [
            Message(role="system", content=rendered),
        ]
        completion = None
        if config.client_style == ClientStyle.ROUNDROBIN.value:
            completion = await CLIENT.chat_completion(
                messages=few_shot_msg,
                stream=False,
                temperature=config.temperature,
            )
        else:
            completion = await self.openai.chat_completion(
                config.model,
                tuple(few_shot_msg),
                temperature=config.temperature,
            )

        return completion

    @rediscache
    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        """generate the template"""

        completion, _ = await self.agen_helper(invoke_id=invoke_id, envs=envs, **kwargs)

        result = completion.content

        result = await self.extract_result(result)

        return {"result": result}


class DecisionTreeEngine(DecisionEngine):
    """decision tree engine"""

    @property
    def template_name(self):
        return "classification.classification_with_context_and_question"

    @property
    def node_id(self):
        return "classification.decision_tree"

    async def agen_helper(self, *, invoke_id=None, envs=None, **kwargs):
        config: DecisionTreeMod = self.config
        context = ""
        if "context" in kwargs:
            context = kwargs["context"]

        assert "question" in kwargs

        current_node = config.root

        level = 0

        while current_node:
            start_time = perf_counter()
            params = {
                "context": context,
                "question": kwargs["question"],
                "amc": kwargs["amc"],
                "product": kwargs["product"],
                "mapping": current_node.mapping,
            }
            template = self.jinja_env.get_template(current_node.template)
            rendered = template.render(**params)
            completion = await self.make_request(rendered)
            hit_key = await self.extract_result(completion.content)
            logging.info(
                "%s decision tree level %d, result %s, extracted key %s",
                invoke_id,
                level,
                completion.content,
                hit_key,
            )

            await self._persist_content(
                envs=envs,
                invoke_id=invoke_id,
                node_id=self.node_id,
                prompt=rendered,
                result=completion.content,
                seconds_spent=perf_counter() - start_time,
                usage=completion.usage,
            )
            current_node = current_node.children.get(hit_key, None)
            level = level + 1

        return completion, rendered


class ClassificationEngine(DecisionEngine):
    """select item number"""

    @property
    def template_name(self):
        return "classification.classification_with_context_and_question"

    @property
    def node_id(self):
        return "classification.classification_list"

    async def agen_helper(self, *, invoke_id=None, envs=None, **kwargs):
        config: ClassificationMod = self.config
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

        template = self.jinja_env.get_template(self.template_name)
        rendered = template.render(**params)
        completion = await self.make_request(rendered)

        return completion, rendered

import json
from itertools import chain
from typing import List

from jinja2 import Environment, FileSystemLoader
from redis import Redis

from config import profile
from kbgpt.lib.templates.rendering.models import (
    Jinja2RedisLoader,
    RedisTemplateProvider,
    TemplateRepo,
)


class TemplateFactory:
    def create(self) -> TemplateRepo:
        redis = Redis.from_url(profile.vector_store.redis_url)
        return TemplateRepo(RedisTemplateProvider(redis))


def init_jinja_env():
    jinja_env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        auto_reload=True,
        loader=Jinja2RedisLoader(),
    )

    def split_lists_str(lst_str: List[str]):
        return "\n---\n".join(lst_str)

    def json_loads(json_str: str):
        return json.loads(json_str)

    def flatten(lst):
        return list(chain.from_iterable(lst))

    jinja_env.filters["split_lists_str"] = split_lists_str
    jinja_env.filters["json_loads"] = json_loads
    jinja_env.filters["flatten"] = flatten
    return jinja_env


JINJA_ENV = init_jinja_env()

JINJA_FS_ENV = Environment(loader=FileSystemLoader("./kbgpt/res/"), auto_reload=False)

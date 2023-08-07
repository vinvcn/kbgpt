from redis import Redis

from config import profile
from kbgpt.lib.templates.rendering.models import RedisTemplateProvider, TemplateRepo


class TemplateFactory:
    def create(self) -> TemplateRepo:
        redis = Redis.from_url(profile.vector_store.redis_url)
        return TemplateRepo(RedisTemplateProvider(redis))

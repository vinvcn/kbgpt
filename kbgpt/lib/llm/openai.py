import datetime
import logging
import os
import threading
from ast import mod
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import openai
from async_lru import alru_cache
from openai.error import RateLimitError
from pydantic import BaseModel, Field
from redis import Redis
from tenacity import stop_after_attempt  # for exponential backoff
from tenacity import retry, wait_random_exponential

from config import profile
from kbgpt.svc.utils.openai import get_total_cost


class Message(BaseModel):
    """messages for a completion call"""

    role: str
    content: str

    class Config:
        frozen = True


class Usage(BaseModel):
    """OpenAI usage object"""

    prompt_tokens: int = Field(0)
    completion_tokens: int = Field(0)
    total_tokens: int = Field(0)
    cost: float = Field(0.0)

    def __init__(self, model: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if model:
            self.cost = get_total_cost(
                model, self.prompt_tokens, self.completion_tokens
            )

    def __add__(self, val2: "Usage") -> "Usage":
        """add method"""
        if not val2:
            return Usage(**self.__dict__)
        return Usage(
            prompt_tokens=self.prompt_tokens + val2.prompt_tokens,
            completion_tokens=self.completion_tokens + val2.completion_tokens,
            total_tokens=self.total_tokens + val2.total_tokens,
            cost=self.cost + val2.cost,
        )


class Completion(BaseModel):
    usage: Optional[Usage]
    prompt: Optional[str]
    content: str
    metadata: Optional[Dict[str, Any]]


class QuotaCounter:
    def __init__(self) -> None:
        self.tracker = {}
        self._lock = threading.Lock()

    def is_model_available(self, model):
        with self._lock:
            if model not in self.tracker:
                return True
            return datetime.datetime.utcnow() > self.tracker[
                model
            ] + datetime.timedelta(minutes=1)

    def record(self, model):
        with self._lock:
            self.tracker[model] = datetime.datetime.utcnow()


QUOTA_COUNTER = QuotaCounter()


class NoModelAvailable(Exception):
    pass


class OpenAI:
    def __init__(self, redis: Redis = None) -> None:
        self.redis = redis

    def get_decorated_openai(self):
        openai.api_key = os.environ["OPENAI_API_KEY"]
        openai.api_type = "open_ai"
        openai.api_version = None
        if profile.openai.proxied:
            openai.api_base = str(profile.openai.api_base_url)
            openai.proxy = str(profile.openai.proxy_url)
        else:
            openai.api_base = str(profile.openai.unproxied_url)
            openai.proxy = None
        return openai

    @alru_cache(maxsize=256, typed=True)
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def chat_completion(
        self,
        model: Union[str, Tuple[str, ...]],
        messages: Tuple[Message, ...],
        stream=False,
        **kwargs,
    ) -> Completion:
        """chat completion"""
        if isinstance(model, str):
            model = [model]
        exc = None
        openai_client = self.get_decorated_openai()
        for model_name in model:
            try:
                if stream:
                    return await openai_client.ChatCompletion.acreate(
                        model=model_name,
                        messages=[m.dict() for m in messages],
                        stream=True,
                        # organization="bullsmart",
                        **kwargs,
                    )
                else:
                    completion = await openai_client.ChatCompletion.acreate(
                        model=model_name,
                        messages=[m.dict() for m in messages],
                        # organization="bullsmart",
                        **kwargs,
                    )

                    usage = Usage(model_name, **completion["usage"])
                    content = completion.choices[0].message["content"]
                    return Completion(usage=usage, content=content)
            except RateLimitError as e:
                exc = e

        raise exc

    @alru_cache(maxsize=256)
    async def embed(self, content: str):
        model = profile.qa.embeddings_model
        result = await self.get_decorated_openai().Embedding.acreate(
            input=content, model=model
        )
        embedding = result["data"][0]["embedding"]
        return embedding

    async def list_models(self):
        result = await self.get_decorated_openai().Model.alist()
        return result

    async def completion(self, *args, **kwargs) -> Completion:
        """
        wrapper of https://platform.openai.com/docs/api-reference/completions/create
        """

        completion = await openai.Completion.acreate(*args, **kwargs)


client = OpenAI()

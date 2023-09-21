import logging
import os
import threading
from enum import Enum
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple, Union

import openai
from openai.error import RateLimitError
from pydantic import BaseModel, Field
from redis import Redis
from tenacity import retry  # for exponential backoff
from tenacity import retry_if_exception_type, stop_after_attempt, wait_fixed

from config import profile
from kbgpt.configs.profiles import AzureAI
from kbgpt.lib.llm.openai import Message
from kbgpt.svc.utils.openai import get_total_cost, token_counts


class ServiceProvider(Enum):
    OPENAI = 0
    AZURE = 1


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


# class OpenAIBroker:
#     def __init__(self) -> None:
#         pass

#     def get_service(self, provider: ServiceProvider = ServiceProvider.OPENAI):
#         match provider:
#             case ServiceProvider.OPENAI:
#                 openai.api_key = os.environ["OPENAI_API_KEY"]
#                 openai.api_type = "open_ai"
#                 if profile.openai.proxied:
#                     openai.api_base = str(profile.openai.api_base_url)
#                     openai.proxy = str(profile.openai.proxy_url)
#                 return openai
#             case ServiceProvider.AZURE:
#                 openai.api_key = os.environ["AZUREAI_API_KEY"]
#                 openai.api_type = "azure"
#                 openai.api_base = str(profile.azureai.api_base)
#                 openai.proxy = None
#                 return openai
#             case _:
#                 raise ValueError("invalid provider type")


class AllClientRateExceedError(Exception):
    pass


class RoundRobinOpenAI:
    def __init__(self, clients) -> None:
        self.clients = clients
        self.client_index = 0
        self._lock = threading.Lock()

    def get_available_client(self):
        with self._lock:
            pick_index = self.client_index
            self.client_index = (
                0
                if self.client_index + 1 >= len(self.clients)
                else self.client_index + 1
            )
            logging.debug("picking client at index %d", pick_index)
            return self.clients[pick_index]

    @retry(
        wait=wait_fixed(2),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(AllClientRateExceedError),
        reraise=True,
    )
    async def chat_completion(
        self,
        **kwargs,
    ) -> Completion:
        exc = None
        for _ in range(len(self.clients)):
            client = self.get_available_client()
            try:
                completion = await client.chat_completion(**kwargs)
            except RateLimitError as e:  # use specific Exception
                exc = e
                continue
            else:
                return completion

        raise AllClientRateExceedError() from exc


class AzureCompletion:
    def __init__(
        self, api_base: str, env_key_name: str, deployment: str, api_version: str
    ) -> None:
        self.env_key_name = env_key_name
        self.deployment = deployment
        self.invoke_params = {
            "api_key": os.environ[self.env_key_name],
            "api_type": "azure",
            "api_version": api_version,
            "api_base": str(api_base),
        }

    def get_decorated_openai(self):
        openai.proxy = None
        return openai

    async def chat_completion(
        self,
        messages: Tuple[Message, ...],
        stream=False,
        callbacks=None,
        **kwargs,
    ) -> Completion:
        openai_client = self.get_decorated_openai()
        if stream:
            assert callbacks
            buffer = StringIO()
            usage = Usage()
            response = await openai_client.ChatCompletion.acreate(
                engine=self.deployment,
                messages=[m.dict() for m in messages],
                stream=True,
                **self.invoke_params,
                **kwargs,
            )
            async for stream_resp in response:
                token = stream_resp["choices"][0]["delta"].get("content", "")
                buffer.write(token)
                for clbk in callbacks:
                    await clbk(token)
            pompt_tokens = token_counts(
                self.deployment, "\n".join([m.content for m in messages])
            )
            comp_tokens = token_counts(self.deployment, buffer.getvalue())
            total_token = pompt_tokens + comp_tokens
            usage.total_tokens = total_token
            return Completion(usage=usage, content=buffer.getvalue())
        else:
            completion = await openai_client.ChatCompletion.acreate(
                engine=self.deployment,
                messages=[m.dict() for m in messages],
                **self.invoke_params,
                **kwargs,
            )

            usage = Usage(self.deployment, **completion["usage"])
            content = completion.choices[0].message["content"]
            return Completion(usage=usage, content=content)

    async def embed(self, content: str):
        model = profile.qa.embeddings_model
        result = self.get_decorated_openai().Embedding.acreate(
            input=content, engine=self.deployment
        )
        embedding = result["data"][0]["embedding"]
        return embedding


class ChatCompletion:
    def __init__(self, model) -> None:
        self.model = model
        self.invoke_params = {
            "api_key": os.environ["OPENAI_API_KEY"],
            "api_type": "open_ai",
            "api_version": None,
            "api_base": str(profile.openai.api_base_url),
        }

    def get_decorated_openai(self):
        if profile.openai.proxied:
            openai.api_base = str(profile.openai.api_base_url)
            openai.proxy = str(profile.openai.proxy_url)
        return openai

    async def chat_completion(
        self,
        messages: Tuple[Message, ...],
        stream=False,
        callbacks=None,
        **kwargs,
    ) -> Completion:
        openai_client = self.get_decorated_openai()
        if stream:
            assert callbacks
            buffer = StringIO()
            usage = Usage()
            response = await openai_client.ChatCompletion.acreate(
                model=self.model,
                messages=[m.dict() for m in messages],
                stream=True,
                **self.invoke_params,
                **kwargs,
            )
            async for stream_resp in response:
                token = stream_resp["choices"][0]["delta"].get("content", "")
                buffer.write(token)
                for clbk in callbacks:
                    await clbk(token)
            pompt_tokens = token_counts(
                self.model, "\n".join([m.content for m in messages])
            )
            comp_tokens = token_counts(self.model, buffer.getvalue())
            total_token = pompt_tokens + comp_tokens
            usage.total_tokens = total_token
            return Completion(usage=usage, content=buffer.getvalue())
        else:
            completion = await openai_client.ChatCompletion.acreate(
                model=self.model,
                messages=[m.dict() for m in messages],
                **self.invoke_params,
                **kwargs,
            )

            usage = Usage(self.model, **completion["usage"])
            content = completion.choices[0].message["content"]
            return Completion(usage=usage, content=content)

    async def embed(self, content: str):
        model = profile.qa.embeddings_model
        result = self.get_decorated_openai().Embedding.acreate(
            input=content, model=model
        )
        embedding = result["data"][0]["embedding"]
        return embedding


OPENAI_GPT4_ENGINES = [ChatCompletion(model=model) for model in profile.qa.recomm_lst]
AZURE_ENGINES = []
for config in profile.azureai:
    for dep in config.deployments:
        AZURE_ENGINES.append(
            AzureCompletion(
                api_base=config.api_base,
                env_key_name=config.env_key_name,
                deployment=dep,
                api_version=config.api_version,
            )
        )

ALL_AVAILABLE_GPT4_ENGINES = [*OPENAI_GPT4_ENGINES, *AZURE_ENGINES]

CLIENT = RoundRobinOpenAI(clients=ALL_AVAILABLE_GPT4_ENGINES)

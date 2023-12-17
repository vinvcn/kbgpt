import asyncio
from enum import Enum
from os import environ
from typing import Any, List

import aiohttp
from pydantic import BaseModel, Field


class KeyProviders(Enum):
    OPENAI = "openai"
    AZURE_JAPAN = "azure_japan"


class Message(BaseModel):
    role: str
    content: str


class Config(BaseModel):
    base_url: str
    proxied: bool = Field(False)
    proxy_url: str = Field("")
    key_provider: KeyProviders

    @property
    def headers(self):
        """create and return default headers"""
        api_key = ""
        if self.key_provider == KeyProviders.OPENAI:
            api_key = environ["OPENAI_API_KEY"]
        elif self.key_provider == KeyProviders.AZURE_JAPAN:
            api_key = environ["JAPAN_EAST_AZUREAI_API_KEY"]
        else:
            raise ValueError(f"{self.key_provider} not supported")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    @property
    def proxy(self):
        return self.proxy_url if self.proxy_url else None


class Embed:
    URL_PATH = "/v1/embeddings"

    def __init__(self, config: Config) -> None:
        self.config = config

    async def __call__(
        self, *, input: str, model: str = "text-embedding-ada-002", **kwds: Any
    ) -> Any:
        """params same with https://platform.openai.com/docs/api-reference/embeddings/create"""

        data = {"input": input, "model": model}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}{self.URL_PATH}",
                headers=self.config.headers,
                json=data,
                proxy=self.config.proxy,
            ) as response:
                resp = await response.json()
                return resp


class Chat:
    """chat client"""

    URL_PATH = "/v1/chat/completions"

    def __init__(self, config: Config) -> None:
        self.config = config

    async def __call__(
        self, *, model: str, messages: List[Message], stream=False, n=1, **kwds: Any
    ) -> Any:
        """params same with https://platform.openai.com/docs/api-reference/chat/create"""
        data = {
            "model": model,
            "messages": [m.dict() for m in messages],
            "n": n,
            **kwds,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}{self.URL_PATH}",
                headers=self.config.headers,
                json=data,
                proxy=self.config.proxy,
            ) as response:
                if stream:
                    return response
                return await response.json()


async def main():
    chat = Chat(
        Config(
            base_url="http://api.openai.com",
            key_provider=KeyProviders.OPENAI,
            proxied=True,
            proxy_url="http://3.6.141.226:8080",
        )
    )

    rst = await chat(
        model="gpt-4-1106-preview",
        messages=[Message(role="user", content="write a random story in 200 words.")],
        # response_format={"type": "json_object"},
    )

    print(rst)

    # embed = Embed(
    #     Config(
    #         base_url="http://api.openai.com",
    #         key_provider=KeyProviders.OPENAI,
    #         proxied=True,
    #         proxy_url="http://3.6.141.226:8080",
    #     )
    # )

    # emb = await embed(input="hello")

    # print(emb)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

from typing import List, Optional

import openai
from pydantic import BaseModel, Field

from kbgpt.svc.utils.openai import get_total_cost


class Message(BaseModel):
    """messages for a completion call"""

    role: str
    content: str


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
    content: str


class OpenAI:
    def __init__(self) -> None:
        pass

    async def chat_completion(self, model: str, messages: List[Message]) -> Completion:
        """chat completion"""
        completion = await openai.ChatCompletion.acreate(
            model=model, messages=[m.dict() for m in messages]
        )

        usage = Usage(model, **completion["usage"])
        content = completion.choices[0].message["content"]
        return Completion(usage=usage, content=content)

    async def list_models(self):
        result = await openai.Model.alist()
        print(result)

    async def completion(self, *args, **kwargs) -> Completion:
        """
        wrapper of https://platform.openai.com/docs/api-reference/completions/create
        """

        completion = await openai.Completion.acreate(*args, **kwargs)

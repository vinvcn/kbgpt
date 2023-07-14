from typing import List

import openai
from pydantic import BaseModel, Field

from kbgpt.svc.utils.openai import get_total_cost


class Message(BaseModel):
    """ messages for a completion call """
    role: str
    content: str


class Usage(BaseModel):
    """ OpenAI usage object """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float = Field(0.0)

    def __init__(self, model: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cost = get_total_cost(model, self.prompt_tokens, self.completion_tokens)

    def __add__(self, val2: "Usage") -> "Usage":
        """ add method """
        return Usage(
            self.prompt_tokens + val2.prompt_tokens,
            self.completion_tokens + val2.completion_tokens,
            self.total_tokens + val2.total_tokens,
            self.cost + val2.cost,
        )


class Completion(BaseModel):
    usage: Usage
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

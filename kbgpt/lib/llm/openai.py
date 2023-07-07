from typing import List

import openai
from pydantic import BaseModel

from kbgpt.svc.utils.openai import get_total_cost


class Message(BaseModel):
    role: str
    content: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float

    def __init__(self, model: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cost = get_total_cost(model, self.prompt_tokens, self.completion_tokens)


class Completion(BaseModel):
    usage: Usage
    content: str


class OpenAI:
    def __init__(self) -> None:
        pass

    async def chat_completion(self, model: str, messages: List[Message]) -> Completion:
        """ chat completion """
        completion = openai.ChatCompletion.acreate(
            model=model, messages=[m.json() for m in messages]
        )

        usage = Usage(**completion["usage"])
        content = completion.choices[0].message["content"]
        return Completion(usage=usage, content=content)

import abc

from pydantic import BaseModel

from kbgpt.api.libs.base_model import OpenAIResponseBase


class Agent(metaclass=abc.ABCMeta):
    """agent that serves"""

    @abc.abstractmethod
    async def analyze(self, req: BaseModel) -> OpenAIResponseBase:
        """analyze the request and provide response"""

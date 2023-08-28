import abc
from typing import Any, Dict

from kbgpt.lib.exec.engines.configs.models import EngineMod


class Engine(metaclass=abc.ABCMeta):
    """engine"""

    def __init__(self, mod: EngineMod) -> None:
        self.config = mod

    @abc.abstractmethod
    async def agenerate(self, *, invoke_id=None, envs=None, **kwargs) -> Dict[str, Any]:
        """generate the template"""

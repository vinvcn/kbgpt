import abc
from typing import Any, Dict


class Engine(metaclass=abc.ABCMeta):
    """engine"""

    @abc.abstractmethod
    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        """generate the template"""

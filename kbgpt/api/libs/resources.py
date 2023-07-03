import abc
from typing import Any, Dict, List

from sanic import Sanic


class LifeCycleMixin(metaclass=abc.ABCMeta):
    """
    resource object that's lifecycle aware
    """

    @abc.abstractmethod
    async def init(self, app: Sanic):
        """
        init the resource
        """

    @abc.abstractmethod
    async def destroy(self, app: Sanic):
        """
        destroy the resource
        """


class ResourceMgr:
    """
    manager class for lifecycle aware objects
    """

    def __init__(self, app: Sanic) -> None:
        """
        constructor
        """
        self.app = app
        self.pool: Dict[str, LifeCycleMixin] = {}
        self.ordered_pool: List[LifeCycleMixin] = []

    def add(self, obj: LifeCycleMixin):
        """
        add objects to pool
        """
        name = type(obj).__name__
        if name in self.pool:
            raise ValueError(f"Object with name '{name}' already exists")
        self.pool[name] = obj
        self.ordered_pool.append(obj)

    def get(self, name: str) -> Any:
        """
        get the resource with given name
        """
        return self.pool.get(name, None)

    async def init_all(self):
        """
        init all resources
        """
        for res in self.ordered_pool:
            await res.init(self.app)

    async def destroy_all(self):
        """
        destroy all resources
        """
        copied = list(self.ordered_pool)
        copied.reverse()
        for res in copied:
            await res.destroy(self.app)

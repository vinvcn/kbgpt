import abc

from kbgpt.lib.exec.engines.engine import Engine


class FactoryCreationFailed(Exception):
    pass


class Factory(metaclass=abc.ABCMeta):
    """engine"""

    @abc.abstractmethod
    def create_from_model(self, mod) -> "Engine":
        """generate the template"""

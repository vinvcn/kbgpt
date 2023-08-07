import abc

from kbgpt.lib.exec.models import CheckerMod, EqCheckerMod, InListCheckerMod


class CheckerFailedException(Exception):
    pass


class Checker(metaclass=abc.ABCMeta):
    def __init__(self, config: CheckerMod) -> None:
        self.config = config

    @abc.abstractmethod
    async def check(self, **kwargs):
        pass


class InListChecker(Checker):
    async def check(self, **kwargs):
        config: InListCheckerMod = self.config

        if config.trg_list and kwargs[config.key] not in config.trg_list:
            raise CheckerFailedException(
                f"value of '{config.key}' should present in list {config.trg_list}"
            )


class EqChecker(Checker):
    async def check(self, **kwargs):
        config: EqCheckerMod = self.config

        if config.trg_value != kwargs[config.key]:
            raise CheckerFailedException(
                f"value of '{config.trg_value}' should equal to {kwargs[config.key]}"
            )

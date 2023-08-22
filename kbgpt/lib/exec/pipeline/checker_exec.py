import abc

from kbgpt.lib.exec.pipeline.checker_models import (
    CheckerMod,
    CheckerTypes,
    EqCheckerMod,
    EvalCheckerMod,
    InListCheckerMod,
)


class CheckerExec:
    def __init__(self, checkers: CheckerTypes) -> None:
        from kbgpt.lib.exec.pipeline.checker_factory import CheckerFactory

        self.checkers = checkers
        self.factory = CheckerFactory()

    async def exec(self, params):
        if not self.checkers:
            return

        if not isinstance(self.checkers, list):
            self.checkers = [self.checkers]

        for mod in self.checkers:
            checker = self.factory.create_from_model(mod)
            await checker.check(**params)


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


class EvalChecker(Checker):
    async def check(self, **kwargs):
        config: EvalCheckerMod = self.config

        context = {self.config.key: kwargs[self.config.key]}
        if config.eval_exp and not eval(
            config.eval_exp, context
        ):  # pylint: disable = eval-used
            raise CheckerFailedException(
                f"evaluation of expression {config.eval_exp} in context {kwargs} was negative"
            )

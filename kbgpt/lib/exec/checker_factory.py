from functools import singledispatchmethod

from kbgpt.lib.exec.engine_checkers import (
    Checker,
    EqChecker,
    EvalChecker,
    InListChecker,
)
from kbgpt.lib.exec.models import (
    CheckerMod,
    EqCheckerMod,
    EvalCheckerMod,
    InListCheckerMod,
)


class CheckerFactory:
    def __init__(self) -> None:
        pass

    @singledispatchmethod
    def create_from_model(self, mod) -> Checker:
        raise NotImplementedError("Not implemented for this type")

    @create_from_model.register
    def create_from_in_list(self, mod: InListCheckerMod) -> InListChecker:
        return InListChecker(mod)

    @create_from_model.register
    def create_eq(self, mod: EqCheckerMod) -> EqChecker:
        return EqChecker(mod)

    @create_from_model.register
    def create_eval(self, mod: EvalCheckerMod) -> EvalChecker:
        return EvalChecker(mod)

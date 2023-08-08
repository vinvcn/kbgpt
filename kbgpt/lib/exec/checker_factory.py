from functools import singledispatchmethod

from kbgpt.lib.exec.engine_checkers import Checker, EqChecker, InListChecker
from kbgpt.lib.exec.models import CheckerMod, EqCheckerMod, InListCheckerMod


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

from functools import singledispatchmethod

from kbgpt.lib.exec.engines import Engine
from kbgpt.lib.exec.engines.configs.models import (
    FunctionOutMod,
    QAOutputMod,
    RecomOutMod,
    RecomOutTransMod,
)
from kbgpt.lib.exec.engines.factory_models import Factory
from kbgpt.lib.exec.qa.engines import (
    FunctionOutput,
    QAOutput,
    RecommOutput,
    RecommOutTransform,
)


class QAEngFactory(Factory):
    @singledispatchmethod
    def create_from_model(self, mod) -> "Engine":
        raise NotImplementedError("No implementation for this data type")

    @create_from_model.register
    def create_from_model_simple(self, mod: QAOutputMod) -> "QAOutput":
        return QAOutput(mod=mod)

    @create_from_model.register
    def create_from_jinja_mod(self, mod: RecomOutMod) -> "RecommOutput":
        return RecommOutput(mod=mod)

    @create_from_model.register
    def _(self, mod: FunctionOutMod) -> "FunctionOutMod":
        return FunctionOutput(mod=mod)

    @create_from_model.register
    def _(self, mod: RecomOutTransMod) -> RecommOutTransform:
        return RecommOutTransform(mod=mod)

from functools import singledispatchmethod
from typing import List

from kbgpt.lib.exec.engines.configs.models import (
    ClassificationMod,
    EmbedMod,
    GraphExecMod,
    JinjaMod,
    SimilaritySearchMod,
    SimpleMod,
    TestMod,
)
from kbgpt.lib.exec.engines.factory_models import Factory, FactoryCreationFailed
from kbgpt.lib.exec.engines.graph import GraphExec
from kbgpt.lib.exec.engines.select_item_number import ClassificationEngine
from kbgpt.lib.exec.qa.factory import QAEngFactory
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.templates.rendering.models import TemplateRepo

from .embed import Embed
from .engine import Engine
from .jinja import Jinja
from .similarity_search import SimilaritySearch
from .simple_engine import SimpleEngine
from .test_engine import TestEngine


class EngineFactory(Factory):
    def __init__(self, temp_repo: TemplateRepo) -> None:
        self.temp_repo: TemplateRepo = temp_repo

    @singledispatchmethod
    def create_from_model(self, mod) -> "Engine":
        raise NotImplementedError("No implementation for this data type")

    @create_from_model.register
    def create_from_model_simple(self, mod: SimpleMod) -> "SimpleEngine":
        return SimpleEngine(config=mod)

    @create_from_model.register
    def create_from_jinja_mod(self, mod: JinjaMod) -> "JinjaMod":
        return Jinja(config=mod)

    @create_from_model.register
    def _(self, mod: GraphExecMod) -> GraphExec:
        return GraphExec(mod=mod)

    @create_from_model.register
    def create_from_model_embed(self, mod: EmbedMod) -> Embed:
        return Embed(config=mod)

    @create_from_model.register
    def create_from_model_similarity_search(
        self, mod: SimilaritySearchMod
    ) -> SimilaritySearch:
        return SimilaritySearch(config=mod)

    @create_from_model.register
    def create_from_model_classification(
        self, mod: ClassificationMod
    ) -> ClassificationEngine:
        return ClassificationEngine(mod=mod)

    @create_from_model.register
    def create_from_test(self, mod: TestMod) -> "TestEngine":
        return TestEngine(confg=mod)


class ChainedFactory(Factory):
    def __init__(self, chain: List[Factory]):
        self.chain = chain

    def create_from_model(self, mod) -> "Engine":
        for facto in self.chain:
            try:
                return facto.create_from_model(mod)
            except:
                pass
        raise FactoryCreationFailed(f"failed to create object for argument {mod}")


CORE_FACTORY = ChainedFactory(
    chain=[EngineFactory(TemplateFactory().create()), QAEngFactory()]
)

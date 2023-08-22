from functools import singledispatchmethod

from kbgpt.lib.exec.engines.configs.models import (
    EmbedMod,
    JinjaMod,
    SimilaritySearchMod,
    SimpleMod,
    TestMod,
)
from kbgpt.lib.templates.rendering.models import TemplateRepo

from .embed import Embed
from .engine import Engine
from .jinja import Jinja
from .similarity_search import SimilaritySearch
from .simple_engine import SimpleEngine
from .test_engine import TestEngine


class EngineFactory:
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
    def create_from_model_embed(self, mod: EmbedMod) -> Embed:
        return Embed(config=mod)

    @create_from_model.register
    def create_from_model_similarity_search(
        self, mod: SimilaritySearchMod
    ) -> SimilaritySearch:
        return SimilaritySearch(config=mod)

    @create_from_model.register
    def create_from_test(self, mod: TestMod) -> "TestEngine":
        return TestEngine(confg=mod)

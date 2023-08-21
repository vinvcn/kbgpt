from functools import singledispatchmethod

from sanic import Sanic

from kbgpt.lib.exec.engines import (
    CommentEngine,
    Embed,
    Engine,
    JinjaEngine,
    ReportEngine,
    SimilaritySearch,
    SimpleEngine,
    TestEngine,
    ToVoiceEngine,
)
from kbgpt.lib.exec.models import (
    CommentEngineMod,
    EmbedEngineMod,
    JinjaEngineMod,
    MapperEngineMod,
    ReportEngineMod,
    SimilaritySearchMod,
    SimpleEngineMod,
    TestEngineMod,
    ToVoiceEngineMod,
)
from kbgpt.lib.templates.rendering.models import TemplateRepo


class EngineFactory:
    def __init__(self, temp_repo: TemplateRepo) -> None:
        self.temp_repo: TemplateRepo = temp_repo

    @singledispatchmethod
    def create_from_model(self, mod) -> "Engine":
        raise NotImplementedError("No implementation for this data type")

    @create_from_model.register
    def create_from_model_simple(self, mod: SimpleEngineMod) -> "SimpleEngine":
        return SimpleEngine(config=mod)

    @create_from_model.register
    def create_from_jinja_mod(self, mod: JinjaEngineMod) -> "JinjaEngineMod":
        return JinjaEngine(config=mod)

    @create_from_model.register
    def create_from_model_embed(self, mod: EmbedEngineMod) -> Embed:
        return Embed(config=mod)

    @create_from_model.register
    def create_from_model_similarity_search(
        self, mod: SimilaritySearchMod
    ) -> SimilaritySearch:
        return SimilaritySearch(config=mod)

    @create_from_model.register
    def create_from_model_comment(self, mod: CommentEngineMod) -> "CommentEngine":
        return CommentEngine(tmp_repo=self.temp_repo)

    @create_from_model.register
    def create_from_model_report(self, mod: ReportEngineMod) -> "ReportEngine":
        return ReportEngine(
            tmp_repo=self.temp_repo, render_config=mod.render_config.copy()
        )

    @create_from_model.register
    def create_from_model_to_voice(self, mod: ToVoiceEngineMod) -> "ToVoiceEngine":
        return ToVoiceEngine()

    @create_from_model.register
    def create_from_test(self, mod: TestEngineMod) -> "TestEngine":
        return TestEngine(confg=mod)

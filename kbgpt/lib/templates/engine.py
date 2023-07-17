"""
engine module
"""
import abc
import asyncio
from datetime import date, datetime, timedelta
from textwrap import indent
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from pydantic import BaseModel

from kbgpt.api.aigc.report_models import Report, Type
from kbgpt.lib.templates import personality
from kbgpt.lib.templates.personality.models import PersonalityRepo
from kbgpt.lib.templates.rendering.models import TemplateRepo
from kbgpt.lib.templates.report.models.daily_data import DailyData
from kbgpt.lib.templates.report.models.weekly_data import WeeklyData
from kbgpt.lib.templates.report.source import (DailyReport, StatsProvider,
                                               WeeklyReport)

# class Op(metaclass=abc.ABCMeta):
#     """
#     Operand
#     """

#     @abc.abstractmethod
#     def perform(self) -> 'Op':
#         """ perform the action undertaken """


# class OpPersonality(Op):

#     def perform(self):
#         pass


# class Operator(Op):
#     """
#     Operator
#     """

#     @property
#     @abc.abstractmethod
#     def operands(self) -> List[Op]:
#         """ list of child operations """


class EngineResult(BaseModel):
    content: str

    metadata: Optional[Dict[str, Any]]


class Engine(metaclass=abc.ABCMeta):
    """engine"""

    @abc.abstractmethod
    async def agenerate(self, *args, **kwargs) -> EngineResult:
        """generate the template"""


class SimpleEngine(Engine):
    """clasify engine"""

    def __init__(self, name: str, tmp_repo: TemplateRepo) -> None:
        super().__init__()
        self.name = name
        self.tmp_repo = tmp_repo

    async def agenerate(self, *args, **kwargs) -> EngineResult:
        rendered = await self.tmp_repo.render(*args, name=self.name, **kwargs)
        return EngineResult(content=rendered)


class CommentEngine(Engine):
    """comment engine"""

    NAME = "virtual_comment"

    def __init__(self, tmp_repo: TemplateRepo):
        super().__init__()
        self.tmp_repo = tmp_repo
        self.p_repo = PersonalityRepo.from_file(self.NAME)

    async def agenerate(self, *args, **kwargs) -> EngineResult:
        v_person = self.p_repo.pick_one()
        rendered = await self.tmp_repo.render(
            *args, name=self.NAME, personality=v_person, **kwargs
        )
        # rendered = self.temp.render(*args, personality=v_person, **kwargs)
        return EngineResult(content=rendered)


class ReportEngine(Engine):
    """report engine"""

    def __init__(self, tmp_repo: TemplateRepo):
        self.tmp_repo = tmp_repo

    async def agenerate(
        self,
        *args,
        data_provider: Callable[..., Awaitable[BaseModel]],
        name: str,
        **kwargs
    ) -> EngineResult:
        """
        generate template
        """

        data = await data_provider()
        result = await self.tmp_repo.render(name=name, data=data.json(indent=4))
        return EngineResult(content=result, metadata={"data": data.json()})

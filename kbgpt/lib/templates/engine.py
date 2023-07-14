"""
engine module
"""
import abc
import asyncio
from datetime import date, datetime, timedelta
from textwrap import indent
from typing import Any, Dict, Tuple

from pydantic import BaseModel

from kbgpt.api.aigc.report_models import Report, Type
from kbgpt.lib.templates.personality.models import PersonalityRepo
from kbgpt.lib.templates.rendering.models import (MOD_TMP_REPO, Template,
                                                  TemplateRepo)
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

    metadata: Dict[str, Any]


class Engine(metaclass=abc.ABCMeta):
    """engine"""

    @abc.abstractmethod
    async def agenerate(self, *args, **kwargs) -> str:
        """generate the template"""


class SimpleEngine(Engine):
    """clasify engine"""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    async def agenerate(self, *args, **kwargs) -> str:
        temp: Template = MOD_TMP_REPO.pick_one(name=self.name)
        rendered = temp.render(*args, **kwargs)
        return rendered


class CommentEngine(Engine):
    """comment engine"""

    def __init__(self):
        super().__init__()
        self.p_repo = PersonalityRepo.from_file("virtual_comment")
        self.temp = asyncio.run(MOD_TMP_REPO.pick_one(name="comment"))

    async def agenerate(self, *args, **kwargs) -> str:
        v_person = self.p_repo.pick_one()
        rendered = self.temp.render(*args, personality=v_person, **kwargs)
        return rendered


class ReportEngine(Engine):
    """report engine"""

    def __init__(self, tmp_repo: TemplateRepo):
        self.tmp_repo = tmp_repo

    async def agenerate(self, *args, dt: date, report_type: Type, **kwargs) -> Tuple[str, BaseModel]:
        """
        generate template
        """

        data = await self.data(report_type, dt)
        result = await self.tmp_repo.render(
            name=f"report_{report_type.value}", data=data.json(indent=4)
        )
        return result, data

    async def data(self, report_type: Type, dt: datetime) -> BaseModel:
        data_provider = DailyReport() if report_type == Type.DAILY else WeeklyReport()
        data: BaseModel = await data_provider(dt=dt)
        return data

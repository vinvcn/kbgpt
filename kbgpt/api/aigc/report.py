"""
report api
"""
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sanic import Blueprint, Request, Sanic
from sanic_ext import openapi, validate

from kbgpt.api.admin.models import TaskStatusResponse
from kbgpt.api.aigc.report_models import Report, ReportResponse, ToVoice, Type
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse, ResponseBase
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.rest.be_admin import BackendAdmin, CreateReport, ReportType, SourceType
from kbgpt.lib.tasks.manager import FuncWrapper, TaskManager, TaskRecord
from kbgpt.svc.aigc.report import ReportAgent, ToVoiceAgent, WeeklyAgent

RP = Blueprint("report", url_prefix="rp")


class GetReportResponse(ResponseBase):
    """report response"""

    results: Optional[List[CreateReport]]


@RP.route("/get_report", methods=["GET"])
@openapi.description("get the report")
@openapi.definition(body={API_CONTENT_TYPE: Report})
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: TaskStatusResponse.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=Report)
async def get_report(request: Request, body: Report):
    try:
        tm: TaskManager = request.app.ctx.res.get(TaskManager.__name__)
        name = (
            WeeklyReport.__name__
            if body.type == Type.WEEKLY
            else DailyReport.__name__
            if body.type == Type.DAILY
            else WeeklyReport.__name__
        )
        record = TaskRecord(
            task_id=str(uuid4()),
            task_name=name,
            task_handle=name,
            parameters=body.json(),
        )
        await tm.add_task(record)
        record = await tm.get_task(record.task_name, record.task_id)
        return jtext(TaskStatusResponse.from_orm(record))
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(error=repr(e)))


@RP.route("/get_report_sync", methods=["GET"])
@openapi.description("get the report")
@openapi.definition(body={API_CONTENT_TYPE: Report})
@openapi.response(
    200,
    {
        API_CONTENT_TYPE: GetReportResponse.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=Report)
async def get_report_sync(request: Request, body: Report):
    try:
        if body.type == Type.WEEKLY or body.type == Type.MONTHLY:
            resp = await WeeklyReport("", "").invoke(app=request.app, body=body)
        else:
            resp = await DailyReport("", "").invoke(app=request.app, body=body)
        return jtext(resp)
    except Exception as e:
        logging.exception(e)
        return jtext(ErrorResponse(error=repr(e)))


class DailyReport(FuncWrapper):
    async def __call__(
        self, *args: Any, app: Sanic, record: TaskRecord, **kwds: Any
    ) -> Any:
        body = Report.parse_raw(record.parameters)
        return await self.invoke(app, body)

    async def invoke(self, app: Sanic, body: Report):
        # pylint: disable=broad-except
        try:
            results = []
            date_str = body.date.strftime("%Y-%m-%d")
            agent = ReportAgent(app=app)
            txt_result: ReportResponse = await agent.analyze(body)
            results = [
                CreateReport(
                    content=txt_result.content,
                    data=txt_result.data,
                    date=date_str,
                    source=SourceType.TEMPLATE.value,
                    type=ReportType.DAILY.value,
                ),
                CreateReport(
                    content=txt_result.polish_content,
                    data=txt_result.data,
                    date=date_str,
                    source=SourceType.AIGC.value,
                    type=ReportType.DAILY.value,
                ),
            ]
            bac_result = await BackendAdmin().create_report(results)
            logging.info(bac_result)
            return GetReportResponse(results=results)
        except Exception as e:
            logging.exception(e)
            logging.error("generating report failed")
            raise e


class WeeklyReport(FuncWrapper):
    def __init__(self, name: str, handle: str):
        super().__init__(name, handle)
        self.config = {
            "coverBreakSec": 1.9,
            "pageBreakSec": 1,
            "listingBreakSec": 2,
            "listingBreakSec1": 1.9,
            "listingBreakSec2": 3,
        }

    async def __call__(
        self, *args: Any, app: Sanic, record: TaskRecord, **kwds: Any
    ) -> Any:
        body = Report.parse_raw(record.parameters)
        return await self.invoke(app=app, body=body)

    def pad_timepoints_for_pages(self, timepoints: Dict[str, Any], pages: List[str]):
        series = timepoints["timepoints"]
        turnpage = self.config["pageBreakSec"]
        page_reading = self.config["listingBreakSec2"]
        offset = series[-1]["endTime"]
        for i in range(len(series), len(pages)):
            series.append(
                {
                    "startTime": offset + turnpage,
                    "index": i,
                    "text": pages[i],
                    "endTime": offset + turnpage + page_reading,
                }
            )
            offset += turnpage + page_reading
        timepoints["totalTime"] = series[-1]["endTime"]
        return json.dumps(timepoints)

    async def invoke(self, app: Sanic, body: Report):
        # pylint: disable=broad-except
        try:
            results = []
            date_str = body.date.strftime("%Y-%m-%d")
            agent = WeeklyAgent(app=app, render_config=self.config)
            txt_result: ReportResponse = await agent.analyze(body)
            tv_agent = ToVoiceAgent(app=app)
            vic_result = await tv_agent.analyze(
                ToVoice(pages=txt_result.pages, ssml=txt_result.ssml)
            )
            report_type = (
                ReportType.WEEKLY if body.type == Type.WEEKLY else ReportType.MONTHLY
            )
            results = [
                CreateReport(
                    caption=self.pad_timepoints_for_pages(
                        vic_result.timepoints, txt_result.pages
                    ),
                    content=txt_result.content,
                    data=txt_result.data,
                    date=date_str,
                    voice=vic_result.uri,
                    source=SourceType.TEMPLATE.value,
                    type=report_type.value,
                ),
                CreateReport(
                    content=txt_result.polish_content,
                    data=txt_result.data,
                    date=date_str,
                    voice=vic_result.uri,
                    source=SourceType.AIGC.value,
                    type=report_type.value,
                ),
            ]
            bac_result = await BackendAdmin().create_report(results)
            logging.info(bac_result)
            return GetReportResponse(results=results)
        except Exception as e:
            logging.exception(e)
            logging.error("generating report failed")
            raise e


# class MonthlyReport(FuncWrapper):
#     async def __call__(
#         self, *args: Any, app: Sanic, record: TaskRecord, **kwds: Any
#     ) -> Any:
#         body = Report.parse_raw(record.parameters)
#         return await self.invoke(app=app, body=body)

#     async def invoke(self, app: Sanic, body: Report):
#         # pylint: disable=broad-except
#         try:
#             results = []
#             date_str = body.date.strftime("%Y-%m-%d")
#             agent = WeeklyAgent(app=app)
#             txt_result: ReportResponse = await agent.analyze(body)
#             tv_agent = ToVoiceAgent(app=app)
#             vic_result = await tv_agent.analyze(
#                 ToVoice(pages=txt_result.pages, ssml=txt_result.ssml)
#             )
#             results = [
#                 CreateReport(
#                     caption=vic_result.timepoints,
#                     content=txt_result.content,
#                     data=txt_result.data,
#                     date=date_str,
#                     voice=vic_result.uri,
#                     source=SourceType.TEMPLATE.value,
#                     type=ReportType.WEEKLY.value,
#                 ),
#                 CreateReport(
#                     content=txt_result.polish_content,
#                     data=txt_result.data,
#                     date=date_str,
#                     voice=vic_result.uri,
#                     source=SourceType.AIGC.value,
#                     type=ReportType.WEEKLY.value,
#                 ),
#             ]
#             bac_result = await BackendAdmin().create_report(results)
#             logging.info(bac_result)
#             return GetReportResponse(results=results)
#         except Exception as e:
#             logging.exception(e)
#             logging.error("generating report failed")
#             raise e

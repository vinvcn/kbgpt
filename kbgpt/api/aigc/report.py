"""
report api
"""
import logging
import traceback
from typing import List, Optional

from sanic import Blueprint, Request, Sanic
from sanic_ext import openapi, validate

from kbgpt.api.aigc.report_models import Report, ReportResponse, ToVoice, Type
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import ErrorResponse, ResponseBase
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.rest.be_admin import BackendAdmin, CreateReport, ReportType, SourceType
from kbgpt.svc.aigc.report import ReportAgent, ToVoiceAgent

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
        API_CONTENT_TYPE: ResponseBase.schema(),
    },
)
@openapi.response(500, {API_CONTENT_TYPE: ErrorResponse.schema()})
@validate(json=Report)
async def get_report(request: Request, body: Report):
    try:
        # request.app.add_task(reporting_task(request.app, body))
        resp = await reporting_task(request.app, body)
        return jtext(resp)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.exception(e)
        error_msg = "".join(traceback.format_exception(e))
        return jtext(ErrorResponse(success=False, error=error_msg))


async def reporting_task(app: Sanic, body: Report):
    """
    kick off reporting
    """
    # pylint: disable=broad-except
    try:
        results = []
        if body.type == Type.WEEKLY:
            agent = ReportAgent(app=app)
            txt_result: ReportResponse = await agent.analyze(body)
            tv_agent = ToVoiceAgent(app=app)
            vic_result = await tv_agent.analyze(ToVoice(**txt_result.__dict__))
            results = [
                CreateReport(
                    content=txt_result.content,
                    data=txt_result.data,
                    voice=vic_result.uri,
                    source=SourceType.TEMPLATE.value,
                    type=ReportType.WEEKLY.value,
                ),
                CreateReport(
                    content=txt_result.polish_content,
                    data=txt_result.data,
                    voice=vic_result.uri,
                    source=SourceType.AIGC.value,
                    type=ReportType.WEEKLY.value,
                ),
            ]
        else:
            agent = ReportAgent(app=app)
            txt_result: ReportResponse = await agent.analyze(body)
            results = [
                CreateReport(
                    content=txt_result.content,
                    data=txt_result.data,
                    source=SourceType.TEMPLATE.value,
                    type=ReportType.DAILY.value,
                ),
                CreateReport(
                    content=txt_result.polish_content,
                    data=txt_result.data,
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

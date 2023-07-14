"""
report api
"""
import logging
import time
import traceback
from json import dumps

from sanic import Blueprint, Request, Sanic
from sanic_ext import openapi, validate
from tenacity import retry, stop_after_attempt, wait_fixed

from kbgpt.api.aigc.qa_models import DocInfo, QAResponse, Question
from kbgpt.api.aigc.report_models import Report, ReportResponse, ToVoice, Type
from kbgpt.api.constants import API_CONTENT_TYPE
from kbgpt.api.libs.base_model import (ErrorResponse, OpenAIResponseBase,
                                       ResponseBase)
from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.api.libs.utils import invoke_agent, jtext
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.rest.be_admin import (BackendAdmin, CreateReport,
                                     CreateReportReq, ReportType)
from kbgpt.svc.aigc.qa.cache_qa_services import ProxiedQAAgent
from kbgpt.svc.aigc.qa.file_services import ProxiedDocAgent
from kbgpt.svc.aigc.qa.qa_services import QAagent
from kbgpt.svc.aigc.report import ReportAgent, ToVoiceAgent

RP = Blueprint("report", url_prefix="rp")


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
        request.app.add_task(warmup_task(request.app, body))
        return jtext(ResponseBase(success=True))
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.exception(e)
        error_msg = "".join(traceback.format_exception(e))
        return jtext(ErrorResponse(success=False, error=error_msg))


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def warmup_task(app: Sanic, body: Report):
    """
    kick off warm up task
    """
    # pylint: disable=broad-except
    try:
        if body.type == Type.WEEKLY:
            agent = ReportAgent(app=app)
            txt_result: ReportResponse = await agent.analyze(body)
            tv_agent = ToVoiceAgent(app=app)
            vic_result = await tv_agent.analyze(ToVoice(**txt_result.__dict__))
            bac_result = await BackendAdmin().create_report(
                CreateReport(
                    content=txt_result.content,
                    data=txt_result.data,
                    voice=vic_result.uri,
                    type=ReportType.WEEKLY.value
                )
            )
            logging.info(bac_result)
        else:
            agent = ReportAgent(app=app)
            txt_result: ReportResponse = await agent.analyze(body)
            bac_result = await BackendAdmin().create_report(
                CreateReport(
                    content=txt_result.content,
                    data=txt_result.data,
                    type=ReportType.DAILY.value
                )
            )
            logging.info(bac_result)
    except Exception as e:
        logging.exception(e)
        logging.warning("cache refreshing cache encountered exception")
        raise e

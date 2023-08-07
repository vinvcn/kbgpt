import datetime
import json
import logging
import re
import tempfile
from datetime import date, datetime, timedelta
from functools import partial
from os.path import basename
from typing import Any, Dict, Tuple
from urllib.parse import urlsplit
from uuid import uuid4

import google.cloud.texttospeech_v1beta1 as texttospeech
from gcloud.aio.storage import Storage
from sanic import Sanic

from config import profile
from kbgpt.api.aigc.report_models import (
    MediaReportResp,
    Report,
    ReportResponse,
    ToVoice,
    ToVoiceResponse,
    Type,
)
from kbgpt.lib.llm.openai import OpenAI
from kbgpt.lib.rest.be_admin import ReportType
from kbgpt.lib.templates.engine import ReportEngine, SimpleEngine
from kbgpt.svc.aigc import Agent


class WeeklyAgent(Agent):
    jinja_template = "report.{}.jinja"
    adjust_template = "report.{}.adjust"
    polish_template = "report.{}.polish"

    def __init__(self, app: Sanic, render_config: Dict[str, Any]) -> None:
        super().__init__()
        self.app = app
        self.report_engine = ReportEngine(
            app.ctx.temp_repo,
            render_config=render_config,
        )

    async def analyze(self, req: Report) -> MediaReportResp:
        ty = req.type.value.lower()
        adjustformat = SimpleEngine(
            self.adjust_template.format(ty),
            self.app.ctx.temp_repo,
            model=profile.report.openai_model,
        )
        polishengine = SimpleEngine(
            self.polish_template.format(ty),
            self.app.ctx.temp_repo,
            model=profile.report.openai_model,
        )
        jinja_with_listing = await self.report_engine.agenerate(
            req.date,
            req,
            self.jinja_template.format(req.type.value.lower()),
            escape=False,
            show_listing=True,
        )
        jinja_no_listing = await self.report_engine.agenerate(
            req.date,
            req,
            self.jinja_template.format(req.type.value.lower()),
            show_listing=False,
        )
        adjust1 = await adjustformat.agenerate(content=jinja_with_listing.content)
        polish1 = await polishengine.agenerate(content=adjust1.content)
        pages = [
            re.sub(r"#TB-.*?-TB#", "", l.strip())
            for l in re.split(r"#PB-.*-PB#", jinja_with_listing.content)
            if l.strip()
        ]
        # keep the ssml tags but remove the marker
        ssml = (
            jinja_no_listing.content.replace("#PB-", "")
            .replace("-PB#", "")
            .replace("#TB-", "")
            .replace("-TB#", "")
        )

        return MediaReportResp(
            content=adjust1.content,
            pages=pages,
            ssml=ssml,
            polish_content=polish1.content,
            data=jinja_with_listing.metadata["data"],
            **adjust1.usage.__dict__,
        )


class ReportAgent(Agent):
    """report agent"""

    jinja_template = "report.{}.jinja"
    adjust_template = "report.{}.adjust"
    polish_template = "report.{}.polish"

    def __init__(self, app: Sanic) -> None:
        super().__init__()
        self.app = app
        self.report_engine = ReportEngine(app.ctx.temp_repo, render_config={})

    async def analyze(self, req: Report) -> ReportResponse:
        """analyze the request and provide response"""
        ty = req.type.value.lower()
        polish_engine = SimpleEngine(
            self.polish_template.format(ty), self.app.ctx.temp_repo
        )
        adjust_format = SimpleEngine(
            self.adjust_template.format(ty), self.app.ctx.temp_repo
        )
        jinja_completion = await self.report_engine.agenerate(
            req.date,
            req,
            self.jinja_template.format(req.type.value.lower()),
            escape=False,
        )
        completion1 = await adjust_format.agenerate(content=jinja_completion.content)
        logging.debug("filled template")
        logging.debug("\n%s", completion1.prompt)
        logging.debug("\n%s", completion1.content)
        if req.polish:
            completion2 = await polish_engine.agenerate(content=completion1.content)

            logging.debug("result")
            logging.debug("\n%s", completion2)
            usage = completion2.usage + completion1.usage
            return ReportResponse(
                content=completion1.content,
                polish_content=completion2.content,
                data=jinja_completion.metadata["data"],
                comp_tokens=usage.completion_tokens,
                **usage.__dict__,
            )
        else:
            usage = completion1.usage
            return ReportResponse(
                content=completion1.content,
                polish_content=completion1.content,
                data=jinja_completion.metadata["data"],
                comp_tokens=usage.completion_tokens,
                **usage.__dict__,
            )


class ToVoiceAgent(Agent):
    def __init__(self, app: Sanic) -> None:
        super().__init__()

    async def upload_file(
        self, file_content, bucket_name, dest_blob_name
    ) -> Tuple[str, datetime]:
        """upload file"""
        async with Storage() as client:
            await client.upload(
                bucket=bucket_name, object_name=dest_blob_name, file_data=file_content
            )
            # await client.upload_from_filename(bucket_name, dest_blob_name, file_path)
            blob = await client.get_bucket(bucket_name).get_blob(dest_blob_name)
            exp_seconds = 604800
            return (
                await blob.get_signed_url(expiration=exp_seconds),
                datetime.utcnow().timestamp() + exp_seconds,
            )

    async def ssml_to_audio(self, ssml_text, lang_code, speak_rate=1):
        # Generates SSML text from plaintext.
        #
        # Given a string of SSML text and an output file name, this function
        # calls the Text-to-Speech API. The API returns a synthetic audio
        # version of the text, formatted according to the SSML commands. This
        # function saves the synthetic audio to the designated output file.
        #
        # Args:
        # ssml_text: string of SSML text
        # outfile: string name of file under which to save audio output
        #
        # Returns:
        # nothing

        # Instantiates a client
        client = texttospeech.TextToSpeechAsyncClient()

        # Sets the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        # Builds the voice request, selects the language code ("en-US") and
        # the SSML voice gender ("MALE")
        voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code, ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )

        # Selects the type of audio file to return
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16, speaking_rate=speak_rate
        )

        request = texttospeech.SynthesizeSpeechRequest(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
            enable_time_pointing=[
                texttospeech.SynthesizeSpeechRequest.TimepointType(1)
            ],
        )

        # Performs the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = await client.synthesize_speech(request=request)

        return response.audio_content, response.timepoints

    def divide_chunks(self, l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i : i + n]

    def timepoints_to_json(self, timepoints, pages):
        for times, txt in zip(self.divide_chunks(timepoints, 2), pages):
            start = round(times[0].time_seconds, 3)
            end = round(times[1].time_seconds, 3)
            idx = re.findall("\d+", times[0].mark_name)[0]
            yield {"startTime": start, "index": int(idx), "text": txt, "endTime": end}

    def gen_timepoints(self, time_result, pages):
        lst = list(self.timepoints_to_json(time_result, pages))
        return {"totalTime": lst[-1]["endTime"], "timepoints": lst}

    async def analyze(self, req: ToVoice) -> ToVoiceResponse:
        audio_content, timepoints = await self.ssml_to_audio(req.ssml, "en_IN", 1.25)

        object_name = f"test/{uuid4()}.wav"
        public_url, exp_at = await self.upload_file(
            audio_content, "kbgpt_reference_bucket", object_name
        )
        json_timepoints = self.gen_timepoints(timepoints, req.pages)

        return ToVoiceResponse(
            uri=public_url, timepoints=json_timepoints, expires=exp_at
        )

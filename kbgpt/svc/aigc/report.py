import datetime
import logging
from datetime import datetime
from os.path import basename
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import google.cloud.texttospeech_v1beta1 as texttospeech
from gcloud.aio.storage import Storage
from sanic import Sanic

from config import profile
from kbgpt.api.aigc.report_models import (
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


class ReportAgent(Agent):
    """report agent"""

    def __init__(self, app: Sanic) -> None:
        super().__init__()
        self.report_engine = ReportEngine(app.ctx.temp_repo)
        self.polish_engine = SimpleEngine("report_polish", app.ctx.temp_repo)
        self.adjust_format = SimpleEngine(
            "report.daily.adjust_space_and_breaks", app.ctx.temp_repo
        )
        self.weekly_format = SimpleEngine(
            "report.weekly.adjust_format", app.ctx.temp_repo
        )
        self.openai = OpenAI()

    async def analyze(self, req: Report) -> ReportResponse:
        """analyze the request and provide response"""

        jinja_completion = await self.report_engine.agenerate(
            req.date, req, f"report_{req.type.value}"
        )
        if req.type == Type.DAILY:
            completion1 = await self.adjust_format.agenerate(
                content=jinja_completion.content
            )
        else:
            pass

        logging.debug("filled template")
        logging.debug("\n%s", completion1.prompt)
        logging.debug("\n%s", completion1.content)
        if req.polish:
            completion2 = await self.polish_engine.agenerate(
                content=completion1.content
            )

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

        return response.audio_content

    async def convert_to_ssml(self, content: str) -> str:
        return f"<speak>{content}</speak>"

    async def analyze(self, req: ToVoice) -> ToVoiceResponse:
        ssml_str = await self.convert_to_ssml(req.content)
        audio_content = await self.ssml_to_audio(ssml_str, "en_IN", 1.25)

        object_name = f"test/{uuid4()}.wav"
        public_url, exp_at = await self.upload_file(
            audio_content, "kbgpt_reference_bucket", object_name
        )
        return ToVoiceResponse(uri=public_url, expires=exp_at)

"""
engine module
"""
import abc
from datetime import date, datetime
from typing import Any, Dict, Tuple
from uuid import uuid4

import google.cloud.texttospeech_v1beta1 as texttospeech
from gcloud.aio.storage import Storage
from jinja2 import Environment

from config import profile
from kbgpt.api.aigc.report_models import Report
from kbgpt.lib.llm.openai import Completion, Message, OpenAI, Usage
from kbgpt.lib.templates.personality.models import PersonalityRepo
from kbgpt.lib.templates.rendering.models import TemplateRepo
from kbgpt.lib.templates.report.source import ReportDataSource


class Engine(metaclass=abc.ABCMeta):
    """engine"""

    @abc.abstractmethod
    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        """generate the template"""


class MapperEngine(Engine):
    """mapper engine"""

    def __init__(self, mapping: Dict[str, Any]) -> None:
        super().__init__()
        self.mapping = mapping

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        obj = kwargs
        renamed = {}
        for k, v in self.mapping.items():
            renamed[v] = obj[k]

        restof = {k: v for k, v in obj.items() if k not in self.mapping}
        return {**renamed, **restof}


class SimpleEngine(Engine):
    """clasify engine"""

    def __init__(self, name: str, tmp_repo: TemplateRepo):
        super().__init__()
        self.name = name
        self.tmp_repo = tmp_repo
        self.openai = OpenAI()

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        rendered = await self.tmp_repo.render(name=self.name, **kwargs)
        completion = await self.openai.chat_completion(
            profile.generative_model, [Message(role="system", content=rendered)]
        )
        completion.prompt = rendered
        return completion.dict()


class CommentEngine(Engine):
    """comment engine"""

    NAME = "virtual_comment"

    def __init__(self, tmp_repo: TemplateRepo):
        super().__init__()
        self.tmp_repo = tmp_repo
        self.p_repo = PersonalityRepo.from_file(self.NAME)
        self.openai = OpenAI()

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        v_person = self.p_repo.pick_one()
        rendered = await self.tmp_repo.render(
            name=self.NAME, personality=v_person, **kwargs
        )
        completion = await self.openai.chat_completion(
            profile.generative_model,
            messages=[Message(role="system", content=rendered)],
        )
        completion.prompt = rendered
        return completion.dict()


class ReportEngine(Engine):
    """report engine"""

    def __init__(self, tmp_repo: TemplateRepo, render_config: Dict[str, Any]):
        self.tmp_repo = tmp_repo
        self.data_source = ReportDataSource()
        self.render_config = render_config

    async def agenerate(self, req: Report, name: str, **kwargs) -> Dict[str, Any]:
        """
        generate template
        """

        data = await self.data_source(req)
        template = await self.tmp_repo.pick_one(name=name)
        jinja_params = {**data.dict(), **self.render_config, **kwargs}
        jtemp = Environment().from_string(template.body)

        completion = Completion(
            prompt=template.body,
            content=jtemp.render(jinja_params),
            usage=Usage(),
            metadata={"data": data.json()},
        )
        return completion.dict()


class ToVoiceEngine(Engine):
    async def ssml_to_audio(self, ssml_text, lang_code, speak_rate=1):
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

    async def agenerate(self, content: str, *args, **kwargs) -> Dict[str, Any]:
        ssml_str = f"<speak>{content}</speak>"
        audio_content = await self.ssml_to_audio(ssml_str, "en_IN", 1.25)

        object_name = f"test/{uuid4()}.wav"
        public_url, exp_at = await self.upload_file(
            audio_content, "kbgpt_reference_bucket", object_name
        )
        completion = Completion(content=public_url)
        return completion.dict()

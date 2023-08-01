"""
engine module
"""
import abc
from datetime import date, datetime
from typing import Any, Callable, Dict, Optional, Tuple
from uuid import uuid4

import google.cloud.texttospeech_v1beta1 as texttospeech
from gcloud.aio.storage import Storage
from jinja2 import Environment
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from config import profile
from kbgpt.api.aigc.report_models import Report, Type
from kbgpt.api.libs.resources import ResourceMgr
from kbgpt.lib.db.mysql import Base, Crud
from kbgpt.lib.llm.openai import Completion, Message, OpenAI, Usage
from kbgpt.lib.templates.personality.models import PersonalityRepo
from kbgpt.lib.templates.rendering.models import TemplateRepo
from kbgpt.lib.templates.report.source import ReportDataSource


class OpenAICompletionRecord(Base):
    __tablename__ = "record_completion_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    prompt = Column(Text(collation="utf8mb4_unicode_ci"))
    completion = Column(Text(collation="utf8mb4_unicode_ci"))
    created_at = Column(DateTime)


def check_cache(func):
    def wrapper(func: Callable):
        async def inner_wrapper(*args, **kwargs):
            from kbgpt.api.app import app

            task_id = None
            if "task_id" not in kwargs:
                task_id = str(uuid4())
            else:
                task_id = kwargs.pop("task_id")

            target_obj = args[0].name

            res: ResourceMgr = app.ctx.res
            crud: Crud = res.get(Crud.__name__)
            record = crud.get_first_by(
                cls=target_obj.__class__,
                filter_params={"task_id": task_id},
                order_col="created_at",
            )
            record


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

    def __init__(
        self, name: str, tmp_repo: TemplateRepo, model: str = profile.generative_model
    ) -> None:
        super().__init__()
        self.name = name
        self.tmp_repo = tmp_repo
        self.model = model
        self.openai = OpenAI()

    async def agenerate(self, *args, **kwargs) -> Completion:
        rendered = await self.tmp_repo.render(*args, name=self.name, **kwargs)
        completion = await self.openai.chat_completion(
            self.model, tuple([Message(role="system", content=rendered)])
        )
        completion.prompt = rendered
        return completion


class CommentEngine(Engine):
    """comment engine"""

    NAME = "virtual_comment"

    def __init__(self, tmp_repo: TemplateRepo):
        super().__init__()
        self.tmp_repo = tmp_repo
        self.p_repo = PersonalityRepo.from_file(self.NAME)
        self.openai = OpenAI()

    async def agenerate(self, *args, **kwargs) -> Completion:
        v_person = self.p_repo.pick_one()
        rendered = await self.tmp_repo.render(
            *args, name=self.NAME, personality=v_person, **kwargs
        )
        completion = await self.openai.chat_completion(
            profile.generative_model,
            messages=[Message(role="system", content=rendered)],
        )
        completion.prompt = rendered
        return completion


class ReportEngine(Engine):
    """report engine"""

    def __init__(self, tmp_repo: TemplateRepo, render_config: Dict[str, Any]):
        self.tmp_repo = tmp_repo
        self.data_source = ReportDataSource()
        self.render_config = render_config

    async def agenerate(
        self, dt: date, req: Report, name: str, escape=True, show_listing=True, **kwargs
    ) -> EngineResult:
        """
        generate template
        """

        data = await self.data_source(dt, req)
        template = await self.tmp_repo.pick_one(name=name)
        jtemp = Environment(autoescape=escape).from_string(template.body)

        return Completion(
            prompt=template.body,
            content=jtemp.render(
                {**data.dict(), **self.render_config, "showListings": show_listing}
            ),
            usage=Usage(),
            metadata={"data": data.json()},
        )


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

    async def agenerate(self, content: str, *args, **kwargs) -> Completion:
        ssml_str = f"<speak>{content}</speak>"
        audio_content = await self.ssml_to_audio(ssml_str, "en_IN", 1.25)

        object_name = f"test/{uuid4()}.wav"
        public_url, exp_at = await self.upload_file(
            audio_content, "kbgpt_reference_bucket", object_name
        )
        return Completion(content=public_url)


class Pipeline:
    async def execulte(
        self,
    ):
        pass

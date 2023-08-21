"""
engine module
"""
import abc
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import google.cloud.texttospeech_v1beta1 as texttospeech
from gcloud.aio.storage import Storage
from jinja2 import Environment
from pydantic import BaseModel

from config import profile
from kbgpt.api.aigc.report_models import Report
from kbgpt.api.libs.callbacks import StreamingAsyncHandler
from kbgpt.lib.db.redis import MyRedis
from kbgpt.lib.db.vector_store import get_embeddings
from kbgpt.lib.exec.models import (
    EmbedEngineMod,
    EngineMod,
    JinjaEngineMod,
    SimilaritySearchMod,
    SimpleEngineMod,
    TestEngineMod,
)
from kbgpt.lib.exec.template_factory import TemplateFactory
from kbgpt.lib.llm.openai import Completion, Message, OpenAI, Usage
from kbgpt.lib.templates.personality.models import PersonalityRepo
from kbgpt.lib.templates.rendering.models import Jinja2RedisLoader, TemplateRepo
from kbgpt.lib.templates.report.source import ReportDataSource


class Engine(metaclass=abc.ABCMeta):
    """engine"""

    @abc.abstractmethod
    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        """generate the template"""


class Embed(Engine):
    """engine that calculates embeddings"""

    def __init__(self, config: EmbedEngineMod) -> None:
        super().__init__()
        self.config = config
        self.openai = OpenAI()

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        assert all([k in kwargs for k in self.config.key_and_labels])
        content = "\n".join(
            f"{l}:\n {kwargs[k]}" if l else kwargs[k]
            for k, l in self.config.key_and_labels.items()
        )
        logging.debug("getting embeddings for content of length %d", len(content))
        embedding = await self.openai.embed(content)
        return {"result": embedding}


class SimilaritySearch(Engine):
    """search redis index for given embedding"""

    def __init__(self, config: SimilaritySearchMod) -> None:
        super().__init__()
        self.config = config
        embedding_func = get_embeddings()
        self.redis: MyRedis = MyRedis.from_existing_index(
            embedding_func, config.index, redis_url=profile.vector_store.redis_url
        )

    async def agenerate(self, embedding: List[float], **kwargs) -> Dict[str, Any]:
        matchings = self.redis.similarity_search_by_vector_with_score(
            embedding, self.config.k
        )
        # map it to string
        # limited = "\n".join(
        #     [
        #         m.content
        #         for m, s in matchings
        #         if s < (self.config.min_threshold if self.config.min_threshold else 1)
        #     ]
        # )
        limited = [
            (m.dict(), s)
            for m, s in matchings
            if s < (self.config.min_threshold if self.config.min_threshold else 1)
        ]
        return {"result": limited}


class JinjaEngine(Engine):
    def __init__(self, config: JinjaEngineMod):
        super().__init__()
        self.config = config
        self.tmp_repo = TemplateFactory().create()
        self.jinja_env = Environment(
            trim_blocks=True, lstrip_blocks=True, loader=Jinja2RedisLoader()
        )
        self.openai = OpenAI()

        def split_lists_str(lst_str: List[str]):
            return "\n---\n".join(lst_str)

        def json_loads(json_str: str):
            return json.loads(json_str)

        self.jinja_env.filters["split_lists_str"] = split_lists_str
        self.jinja_env.filters["json_loads"] = json_loads

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        assert all(
            [k in kwargs for k in self.config.keys_in]
        ), f"keys required but not in params {set(self.config.keys_in) - set(kwargs.keys())}"

        template = self.jinja_env.get_template(self.config.name)
        rendered = template.render(**kwargs)
        if not self.config.stream:
            completion = await self.openai.chat_completion(
                self.config.models[0], tuple([Message(role="system", content=rendered)])
            )

            return {"result": completion.content}
        else:
            assert "callbacks" in kwargs
            request = await self.openai.chat_completion(
                self.config.models[0],
                tuple([Message(role="system", content=rendered)]),
                stream=True,
            )
            buffer = ""
            callbacks: List[StreamingAsyncHandler] = kwargs["callbacks"]
            async for stream_resp in request:
                token = stream_resp["choices"][0]["delta"].get("content", "")
                buffer += token
                for cb in callbacks:
                    await cb.on_llm_new_token(token)
            return {"result": buffer}


class SimpleEngine(Engine):
    """clasify engine"""

    def __init__(self, config: SimpleEngineMod):
        super().__init__()
        self.config = config
        self.tmp_repo = TemplateFactory().create()
        self.openai = OpenAI()

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        assert all(
            [k in kwargs for k in self.config.keys_in]
        ), f"keys required but not in params {set(self.config.keys_in) - set(kwargs.keys())}"

        rendered = await self.tmp_repo.render(name=self.config.name, **kwargs)
        completion = await self.openai.chat_completion(
            self.config.models[0], tuple([Message(role="system", content=rendered)])
        )
        completion.prompt = rendered
        return {"result": completion.content}


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


class TestEngine(Engine):
    def __init__(self, confg: TestEngineMod) -> None:
        super().__init__()
        self.mod = confg

    async def agenerate(self, **kwargs) -> Dict[str, Any]:
        logging.info("params:\n%s", json.dumps(kwargs))
        for k in self.mod.input_keys:
            assert k in kwargs, f"key '{k}' must be present in params"
            logging.info("reading input value: %s", kwargs[k])

        return self.mod.output

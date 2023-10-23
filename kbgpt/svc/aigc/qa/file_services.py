import logging
import uuid
from os import listdir, pardir
from os.path import abspath, dirname, isfile, join
from typing import Any, List
from uuid import uuid4

from aiofiles import open as aopen
from aiofiles import tempfile
from redis.exceptions import LockError
from sanic import Request, Sanic
from sanic.response import JSONResponse

from config import profile
from kbgpt.api.admin.models import TaskStatusResponse
from kbgpt.api.aigc.qa_models import FileProcessResponse, UpdateFromDb
from kbgpt.api.libs.base_model import ErrorResponse, OpenAIResponseBase
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql.process_file_record import ProcessFileRecord
from kbgpt.lib.exec.clients.redis import REDIS_CLIENT
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer
from kbgpt.lib.logging import alog
from kbgpt.lib.tasks.manager import FuncWrapper, TaskManager, TaskRecord


async def add_file_to_customer_service(path: str, **kwargs):
    """
    add a file to the customer service index"""
    indexer = CustomerServiceFilesIndexer()
    await indexer.add_file_to_index(path=path, **kwargs)


async def add_files(paths: List[str]):
    """
    add files in paths"""
    flush = profile.indexing.flush_before_write
    for path in paths:
        logging.debug("adding %s", path)
        await add_file_to_customer_service(path=path, flush_index=flush)
        flush = False


async def add_kb():
    """
    add knowledge base in kb folder"""
    kb_dir = join(dirname(abspath(__file__)), pardir, "kb")
    files = [join(kb_dir, f) for f in listdir(kb_dir)]
    files = [f for f in files if isfile(f) and f.endswith(".txt")]
    await add_files(files)


@alog(ProcessFileRecord)
async def add_files_to_customer_service(
    paths: List[str], business_type: str, ctx=None, **kwargs
):
    """
    transcational add files to the customer service index
    """
    indexer = CustomerServiceFilesIndexer()
    return await indexer.transactional_add_to_index(
        paths=paths, business_type=business_type, **kwargs
    )


class WarmupTask(FuncWrapper):
    """warm up task"""

    def __init__(self, name: str, handle: str):
        super().__init__(name, handle)

    async def __call__(self, *args: Any, app: Sanic, record: TaskRecord, **kwds: Any):
        """
        kick off warm up task
        """
        cache: RedisCacheStoreStrategy = app.ctx.redicache
        # pylint: disable=broad-except
        try:
            await cache.refresh_cache()
        except LockError as e:
            logging.exception(e)
            logging.warning(
                "aquiring lock failed, another thread might be working aborting"
            )
        except Exception as e:
            logging.exception(e)
            logging.warning("cache refreshing cache encountered exception")
            raise e


class ProxiedDocAgent:
    """
    Wrapper for all Doc and Cache logic
    """

    async def process_request_and_refresh_cache(
        self, sanic_app: Sanic, update_db: UpdateFromDb, is_refresh: bool = False
    ):
        try:
            async with tempfile.TemporaryDirectory() as temp_dir:
                paths = []
                for txt_mtl in update_db.items:
                    fname = str(uuid.uuid4())
                    path = f"{temp_dir}/{fname}.txt"
                    async with aopen(path, "w", encoding="utf-8") as f:
                        await f.write(txt_mtl.text_content)
                        await f.flush()
                        paths.append(path)
                await add_file_to_customer_service(
                    paths, flush_index=False, ctx=None, business_type="qa"
                )
                indexes = sanic_app.ctx.cache["indexes"]
                REDIS_CLIENT.reset_all_indexes(indexes=indexes)
        except Exception as e:
            logging.exception(e)
            return jtext(ErrorResponse(success=False, error=str(e)))

    async def process_file_and_refresh_cache(
        self, sanic_app: Sanic, request: Request, is_refresh: bool = False
    ) -> JSONResponse:
        """
        process file then refresh the cache
        """
        # pylint: disable=broad-except
        try:
            async with tempfile.TemporaryDirectory() as temp_dir:
                paths = []
                for file in request.files["file"]:
                    if len(file.body) <= 0:
                        raise ValueError(f"File {file.name} can not be empty")
                    path = f"{temp_dir}/{file.name}"
                    logging.debug("writing to temp file %s", path)
                    async with aopen(path, "wb") as f:
                        await f.write(file.body)
                        await f.flush()
                        paths.append(path)

                logging.info("adding files to customer service %s\n", "\n".join(paths))
                params = {k: v[0] for k, v in request.form.items()}
                await add_files_to_customer_service(
                    paths, flush_index=True, ctx=sanic_app.ctx, **params
                )
                indexes = sanic_app.ctx.cache["indexes"]
                REDIS_CLIENT.reset_all_indexes(indexes=indexes)
            return jtext(
                FileProcessResponse(
                    success=True, msg="Indexes reset" + ",".join(indexes)
                )
            )
        except Exception as e:
            logging.exception(e)
            return jtext(ErrorResponse(success=False, error=str(e)))

    async def refresh_cache(
        self, sanic_app: Sanic, request: Request
    ) -> TaskStatusResponse:
        """
        Trigger a refresh cache task
        """
        # pylint: disable=broad-except
        try:
            tm: TaskManager = request.app.ctx.res.get(TaskManager.__name__)
            name = WarmupTask.__name__
            record = TaskRecord(
                task_id=str(uuid4()), task_name=name, task_handle=name, parameters="{}"
            )
            await tm.add_task(record)
            record = await tm.get_task(record.task_name, record.task_id)
            return jtext(TaskStatusResponse.from_orm(record))
        except Exception as e:
            logging.exception(e)
            return jtext(ErrorResponse(success=False, error=str(e)))

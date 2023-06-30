"""
file service
"""
import logging
from os import listdir, pardir
from os.path import abspath, dirname, isfile, join
from typing import List

from aiofiles import open as aopen
from aiofiles import tempfile
from redis.exceptions import LockError
from sanic import Request, Sanic
from sanic.response import JSONResponse, json
from tenacity import retry, stop_after_attempt, wait_fixed

from config import profile
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql.process_file_record import ProcessFileRecord
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer
from kbgpt.lib.logging import alog


async def add_kb():
    """
    add knowledge base in kb folder"""
    kb_dir = join(dirname(abspath(__file__)), pardir, "kb")
    files = [join(kb_dir, f) for f in listdir(kb_dir)]
    files = [f for f in files if isfile(f) and f.endswith(".txt")]
    await add_files(files)


async def add_files(paths: List[str]):
    """
    add files in paths"""
    flush = profile.indexing.flush_before_write
    for path in paths:
        logging.debug("adding %s", path)
        await add_file_to_customer_service(path=path, flush_index=flush)
        flush = False


async def add_file_to_customer_service(path: str, **kwargs):
    """
    add a file to the customer service index"""
    indexer = CustomerServiceFilesIndexer()
    await indexer.add_file_to_index(path=path, **kwargs)


@alog(ProcessFileRecord)
async def add_files_to_customer_service(paths: List[str], **kwargs):
    """
    transcational add files to the customer service index
    """
    indexer = CustomerServiceFilesIndexer()
    return await indexer.transactional_add_to_index(paths=paths, **kwargs)


async def a_add_file_to_customer_service(**kwargs):
    """
    add a file to the customer service index"""
    add_file_to_customer_service(**kwargs)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def warmup_task(app:Sanic):
    """
    kick off warm up task
    """
    cache:RedisCacheStoreStrategy = app.ctx.redicache
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
                await add_files_to_customer_service(paths, flush_index=True)
            if is_refresh:
                sanic_app.add_task(warmup_task(sanic_app))
            return json({"success": True})
        except Exception as e:
            logging.exception(e)
            return json({"success": False, "error": str(e)})

    async def refresh_cache(self, sanic_app: Sanic, request: Request) -> JSONResponse:
        """
        Trigger a refresh cache task
        """
        # pylint: disable=broad-except
        try:
            sanic_app.add_task(warmup_task(sanic_app))
            return json({"success": True})
        except Exception as e:
            logging.exception(e)
            return json({"success": False, "error": str(e)})



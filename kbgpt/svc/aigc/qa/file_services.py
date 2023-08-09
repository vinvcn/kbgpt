import logging
from os import listdir, pardir
from os.path import abspath, dirname, isfile, join
from typing import List

from aiofiles import open as aopen
from aiofiles import tempfile
from redis.exceptions import LockError
from sanic import Request, Sanic
from sanic.response import JSONResponse
from tenacity import retry, stop_after_attempt, wait_fixed

from config import profile
from kbgpt.api.libs.base_model import ErrorResponse, OpenAIResponseBase
from kbgpt.api.libs.utils import jtext
from kbgpt.lib.db.cache_store import RedisCacheStoreStrategy
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.db.mysql.process_file_record import ProcessFileRecord
from kbgpt.lib.db.vector_store import BusinessType
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer
from kbgpt.lib.logging import alog
from kbgpt.svc.aigc.qa.product_services import ProductImportService


@alog(ProcessFileRecord)
async def add_files_to_customer_service(
    paths: List[str], business_type: str, ctx=None, **kwargs
):
    """
    transcational add files to the customer service index
    """
    if BusinessType(business_type) == BusinessType.QA:
        indexer = CustomerServiceFilesIndexer()
        return await indexer.transactional_add_to_index(paths=paths, **kwargs)
    else:
        crud = ctx.res.get(Crud.__name__)
        import_service = ProductImportService(crud)
        await import_service.csv_to_mysql(paths)
        return await import_service.csv_to_redis(
            paths=paths, business_type=business_type, **kwargs
        )


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def warmup_task(app: Sanic):
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
            return jtext(OpenAIResponseBase(success=True))
        except Exception as e:
            logging.exception(e)
            return jtext(ErrorResponse(success=False, error=str(e)))

    async def refresh_cache(self, sanic_app: Sanic, request: Request) -> JSONResponse:
        """
        Trigger a refresh cache task
        """
        # pylint: disable=broad-except
        try:
            sanic_app.add_task(warmup_task(sanic_app))
            return jtext(OpenAIResponseBase(success=True))
        except Exception as e:
            logging.exception(e)
            return jtext(ErrorResponse(success=False, error=str(e)))

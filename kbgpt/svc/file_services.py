import tempfile

from config import *
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer


def add_file_to_customer_service(path: str):
    indexer = CustomerServiceFilesIndexer(GENERATIVE_MODEL)
    indexer.add_file_to_index(path=path, index_name=CUSTOMER_SERVICE_INDEX, redis_url=REDIS_URL, db_url=DB_URL)

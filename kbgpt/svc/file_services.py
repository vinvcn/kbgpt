import logging
import os
import tempfile
from os import listdir, pardir
from os.path import abspath, dirname, isfile, join
from typing import List

from config import *
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer


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
    flush = FLUSH_BEFORE_WRITE
    for path in paths:
        logging.debug("adding %s" % path)
        await add_file_to_customer_service(path=path, flush_index=flush)
        flush = False


async def add_file_to_customer_service(path: str, **kwargs):
    """
    add a file to the customer service index"""
    indexer = CustomerServiceFilesIndexer()
    await indexer.add_file_to_index(path=path, **kwargs)


async def a_add_file_to_customer_service(**kwargs):
    """
    add a file to the customer service index"""
    add_file_to_customer_service(**kwargs)

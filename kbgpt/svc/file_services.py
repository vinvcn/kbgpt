import logging
import os
import tempfile
from os import listdir, pardir
from os.path import abspath, dirname, isfile, join

from config import *
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer


async def add_kb():
    """
    add knowledge base in kb folder"""
    kb_dir = join(dirname(abspath(__file__)), pardir, "kb")
    files = listdir(kb_dir)
    flush = FLUSH_BEFORE_WRITE
    for filename in files:
        filepath = join(kb_dir, filename)
        logging.debug("adding %s" % filepath)
        if isfile(filepath) and filepath.endswith(".txt"):
            await add_file_to_customer_service(path=filepath, flush_index=flush)
            flush = False


async def add_file_to_customer_service(path: str, **kwargs):
    """
    add a file to the customer service index"""
    indexer = CustomerServiceFilesIndexer(GENERATIVE_MODEL)
    await indexer.add_file_to_index(path=path, **kwargs)


async def a_add_file_to_customer_service(**kwargs):
    """
    add a file to the customer service index"""
    add_file_to_customer_service(**kwargs)

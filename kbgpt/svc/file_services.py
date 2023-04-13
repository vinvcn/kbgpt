import logging
import os
import tempfile
from os import listdir, pardir
from os.path import abspath, dirname, isfile, join

from config import *
from kbgpt.lib.indexing.indexer import CustomerServiceFilesIndexer


def add_kb():
    """
    add knowledge base in kb folder"""
    kb_dir = join(dirname(abspath(__file__)), pardir, "kb")
    files = listdir(kb_dir)
    flush = True
    for filename in files:
        filepath = join(kb_dir, filename)
        logging.debug("adding %s" % filepath)
        if isfile(filepath) and filepath.endswith(".txt"):
            add_file_to_customer_service(path=filepath, flush_index=flush)
            flush = False


def add_file_to_customer_service(path: str, **kwargs):
    """
    add a file to the customer service index"""
    indexer = CustomerServiceFilesIndexer(GENERATIVE_MODEL)
    indexer.add_file_to_index(
        path=path, index_name=CUSTOMER_SERVICE_INDEX, redis_url=REDIS_URL, db_url=DB_URL, **kwargs
    )

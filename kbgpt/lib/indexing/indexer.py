"""
indexers
"""
import abc
import logging
import re
from typing import List

from langchain.docstore.document import Document
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredURLLoader,
    UnstructuredWordDocumentLoader,
)

from kbgpt.lib.db.vector_store import create_vector_store_strategy
from kbgpt.lib.indexing.double_line_breaks_splitter import PondAstonPondSplitter


class AbstractIndexer(metaclass=abc.ABCMeta):
    """
    Abstract indexer class that defines the interface for indexing files.
    """

    EXT_TO_LOADER_MAP = {
        r"https?://.*": lambda p: UnstructuredURLLoader([p]),
        r".*\.pdf": PyPDFLoader,
        r".*\.txt": TextLoader,
        r".*\.html": UnstructuredHTMLLoader,
        r".*\.htm": UnstructuredHTMLLoader,
        r".*\.shtml": UnstructuredHTMLLoader,
        r".*\.docx": UnstructuredWordDocumentLoader,
        r".*\.doc": UnstructuredWordDocumentLoader,
    }

    def _get_loader_for_file(self, path: str) -> TextLoader:
        """
        get the loader for the given file
        """
        for regex, loader in self.EXT_TO_LOADER_MAP.items():
            if re.match(regex, path):
                return loader(path)
        raise ValueError(f"no loader found for {path}")

    @abc.abstractmethod
    def load_and_split(self, path: str, **kwargs) -> List[Document]:
        """
        load the file and split it into documents
        """

    async def add_file_to_index(
        self,
        path: str,
        flush_index: bool = False,
        **kwargs,
    ):
        """
        add a file to the given index
        """
        # with UniqueFilePerIndex(path, db_url, index_name):
        logging.debug("embedding the file")
        # load the data
        documents = self.load_and_split(path)
        store = create_vector_store_strategy(**kwargs)
        await store.write_to_store(documents, flush_index, **kwargs)


class CustomerServiceFilesIndexer(AbstractIndexer):
    """
    Indexer for customer service files
    """

    def __init__(self, tokenize_model: str) -> None:
        super().__init__()
        self.tokenize_model = tokenize_model

    def load_and_split(self, path: str, **kwargs) -> List[Document]:
        """
        load the file and split it into documents
        """
        loader = self._get_loader_for_file(path)
        documents = loader.load_and_split(PondAstonPondSplitter(encoding_model=self.tokenize_model, **kwargs))
        return [d for d in documents if len(d.page_content.strip()) > 0]

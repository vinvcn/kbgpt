"""
indexers
"""
import abc
import logging
import re
from typing import List, Tuple

from langchain.docstore.document import Document
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredURLLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter

from config import profile
from kbgpt.lib.db.vector_store import create_vector_store_strategy
from kbgpt.lib.indexing.double_line_breaks_splitter import PondAstonPondSplitter


class AbstractIndexer(metaclass=abc.ABCMeta):
    """
    Abstract indexer class that defines the interface for indexing files.
    """

    # recursive character splitter
    RECR_SPL = RecursiveCharacterTextSplitter(
        chunk_size=profile.embedding.text_embedding_chunk_size,
        chunk_overlap=profile.embedding.text_embedding_chunk_overlap,
    )
    # customed splitter that splits on "#!#"
    PAP_SPL = PondAstonPondSplitter(encoding_model=profile.qa.generative_model)

    EXT_TO_LOADER_MAP = {
        r"https?://.*": (lambda p: UnstructuredURLLoader([p]), RECR_SPL),
        r".*\.pdf": (PyPDFLoader, RECR_SPL),
        r".*\.kb\.txt": (TextLoader, PAP_SPL),
        r".*\.txt": (TextLoader, RECR_SPL),
        r".*\.html": (UnstructuredHTMLLoader, RECR_SPL),
        r".*\.htm": (UnstructuredHTMLLoader, RECR_SPL),
        r".*\.shtml": (UnstructuredHTMLLoader, RECR_SPL),
        r".*\.docx": (UnstructuredWordDocumentLoader, RECR_SPL),
        r".*\.doc": (UnstructuredWordDocumentLoader, RECR_SPL),
    }

    def _get_loader_and_split(
        self, path: str
    ) -> Tuple[TextLoader, TextSplitter]:
        """
        get the loader for the given file
        """
        for regex, tup in self.EXT_TO_LOADER_MAP.items():
            loader, splitter = tup
            if re.match(regex, path):
                logging.info("matching loader: %s for path: %s", loader, path)
                logging.info(
                    "matching splitter: %s for path: %s", splitter, path
                )
                return loader(path), splitter
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

    def load_and_split(self, path: str, **kwargs) -> List[Document]:
        """
        load the file and split it into documents
        """
        loader, splitter = self._get_loader_and_split(path)
        documents = loader.load_and_split(splitter)
        return [d for d in documents if len(d.page_content.strip()) > 0]

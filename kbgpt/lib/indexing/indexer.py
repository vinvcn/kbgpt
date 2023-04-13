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
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.vectorstores.redis import Redis

from kbgpt.lib.db.unique_file_per_index_ctx import UniqueFilePerIndex
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

    def add_file_to_index(
        self, path: str, index_name: str, redis_url: str, db_url: str, flush_index: bool = False, **kwargs
    ):
        """
        add a file to the given index
        """
        # with UniqueFilePerIndex(path, db_url, index_name):
        logging.debug("embedding the file")
        # load the data
        documents = self.load_and_split(path, **kwargs)
        # flush the index if needed
        if flush_index:
            Redis.drop_index(index_name=index_name, delete_documents=True, redis_url=redis_url)
        # create the retriever
        self._add_docs_to_redis_index(documents, redis_url, index_name)

    def _add_docs_to_redis_index(
        self, documents: List[Document], redis_url: str, index_name: str
    ) -> VectorStoreRetriever:
        """
        create a function that embed the given documents, and creates the retreiver
        """
        rds = Redis.from_documents(documents, OpenAIEmbeddings(), redis_url=redis_url, index_name=index_name)
        retriever = rds.as_retriever(search_type="similarity_limit")
        return retriever


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


# def create_redis_retriever(
#     path: str,
#     db_url: str,
#     redis_url: str,
#     index_name: str,
#     trunksize: int,
#     overlap: int,
# ):
#     """
#     create a retriever from the given path
#     """
#     retriever = None
#     # create a file record
#     with UniqueFilePerIndex(path, db_url, index_name) as (
#         file_record,
#         session,
#     ):
#         if not file_record.embedding:
#             logging.debug("embedding the file")
#             # load the data
#             documents = load_and_split(path, trunksize, overlap)
#             # create the retriever
#             retriever = create_redis_retriver_for_docs(documents, redis_url, index_name)
#         else:
#             logging.debug("using the existing embedding")
#             retriever = create_redis_retriver_for_index_name(redis_url, index_name)

#     return retriever


# create a function that loads the data and returns a retriever
# decide the type of loader and the type of text splitter based on the file extension
# if the file extension is .pdf, use PyPDFLoader and TokenTextSplitter
# if the file extension is .txt, use TextLoader and TokenTextSplitter
# if the file extension is .html, use UnstructuredHTMLLoader and TokenTextSplitter
# if the file extension is .htm, use UnstructuredHTMLLoader and TokenTextSplitter
# if the path is an url (starts with http), use UnstructuredURLLoader and TokenTextSplitter
# def load_and_split(path: str, trunksize: int, overlap: int) -> List[Document]:
#     """
#     load and split method
#     """
#     if path.startswith("http"):
#         loader = UnstructuredURLLoader([path])
#         data = loader.load_and_split(TokenTextSplitter(chunk_size=trunksize, chunk_overlap=overlap))
#     elif path.endswith(".pdf"):
#         loader = PyPDFLoader(path)
#         data = loader.load_and_split(TokenTextSplitter(chunk_size=trunksize, chunk_overlap=overlap))
#     elif path.endswith(".txt"):
#         loader = TextLoader(path)
#         data = loader.load_and_split(TokenTextSplitter(chunk_size=trunksize, chunk_overlap=overlap))
#     elif path.endswith(".html") or path.endswith(".htm"):
#         loader = UnstructuredHTMLLoader(path)
#         data = loader.load_and_split(TokenTextSplitter(chunk_size=trunksize, chunk_overlap=overlap))
#     else:
#         raise ValueError(f"path {path} not supported")

#     return data


# @contextmanager
# def create_or_fetch_file_record(
#     path: str, db_url: str, redis_index: str
# ) -> Tuple[FileRecord, sessionmaker]:
#     """
#     create a context manager that creates a file record if it does not exist
#     """
#     engine = create_engine(db_url, echo=True)
#     Session = sessionmaker(bind=engine)
#     session = Session()
#     try:
#         digest = None
#         file_record = None
#         content_type = ContentType.get_content_type(path)

#         if content_type == ContentType.URL:
#             digest = md5_url_content(path)
#         else:
#             digest = md5_file_content(path)

#         # check if the file record exists
#         # check on both the hashing and the redis index
#         file_record = (
#             session.query(FileRecord)
#             .filter(FileRecord.hashing == digest)
#             .filter(FileRecord.redis_index == redis_index)
#             .one_or_none()
#         )
#         if file_record is not None:
#             yield file_record, session
#             file_record.embedding = True
#         else:
#             # get the name of the file from the path, normalize it to lower case
#             # and replace all spaces with underscore
#             normalized_name = path.split("/")[-1].lower().replace(" ", "_")
#             file_record = FileRecord(
#                 name=normalized_name,
#                 path=path,
#                 redis_index=redis_index,
#                 content_type=content_type.value,
#                 hashing=digest,
#                 embedding=False,
#             )
#             yield file_record, session
#             file_record.embedding = True

#     except Exception as e:
#         raise e
#     finally:
#         if file_record.id is None:
#             session.add(file_record)
#         else:
#             session.merge(file_record)
#         session.commit()

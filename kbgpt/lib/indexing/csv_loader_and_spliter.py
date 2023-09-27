import json
from csv import DictReader
from os.path import basename
from typing import List, Optional

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class CSVTextLoader(BaseLoader):
    """Load csv files"""

    def __init__(self, file_path: str, encoding: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        self.encoding = encoding if encoding else "utf-8"

    def load(self) -> List[Document]:
        """load from file path"""
        documents = []
        with open(self.file_path, "r", encoding=self.encoding) as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                page_content = "\n".join([f"{k}: {v}" for k, v in row.items()])
                documents.append(
                    Document(
                        page_content=page_content,
                        metadata={"source": basename(self.file_path)},
                    )
                )
            return documents


class CSVJSONLoader(BaseLoader):
    """Load csv files"""

    def __init__(self, file_path: str, encoding: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        self.encoding = encoding if encoding else "utf-8"

    def load(self) -> List[Document]:
        """load from file path"""
        documents = []
        with open(self.file_path, "r", encoding=self.encoding) as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                documents.append(
                    Document(
                        page_content=json.dumps(row, indent=4),
                        metadata={"source": basename(self.file_path)},
                    )
                )
            return documents

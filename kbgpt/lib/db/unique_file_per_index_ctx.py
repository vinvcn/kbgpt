import logging
from typing import Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from kbgpt.lib.db.file_record import FileRecord
from kbgpt.lib.utils import ContentType, md5_file_content, md5_url_content


class UniqueFilePerIndex:
    """
    context manager that raises an error if a file is already indexed
    """

    def __init__(self, path: str, db_url: str, redis_index: str):
        self.path = path
        self.redis_index = redis_index
        Session = sessionmaker(bind=create_engine(db_url, echo=True))
        self.session = Session()
        self.file_record = None

    def __enter__(self) -> Tuple[FileRecord, sessionmaker]:
        logging.debug("entering context manager for %s", self.path)
        digest = None
        content_type = ContentType.get_content_type(self.path)

        if content_type == ContentType.URL:
            digest = md5_url_content(self.path)
        else:
            digest = md5_file_content(self.path)

        logging.debug("digest for %s is %s", self.path, digest)

        # check if the file record exists
        # check on both the hashing and the redis index
        self.file_record = (
            self.session.query(FileRecord)
            .filter(FileRecord.hashing == digest)
            .filter(FileRecord.redis_index == self.redis_index)
            .one_or_none()
        )
        logging.debug("file record for %s is %s", self.path, self.file_record)
        if self.file_record is None:
            logging.debug("file record for %s is None, creating new one", self.path)
            # get the name of the file from the path, normalize it to lower case
            # and replace all spaces with underscore
            normalized_name = self.path.split("/")[-1].lower().replace(" ", "_")
            self.file_record = FileRecord(
                name=normalized_name,
                path=self.path,
                redis_index=self.redis_index,
                content_type=content_type.value,
                hashing=digest,
                embedding=False,
            )
            return self.file_record, self.session

        if self.file_record.embedding:
            raise ValueError(f"file {self.path} already indexed")

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug("exiting context manager for %s", self.path)
        if exc_type is None:
            self.file_record.embedding = True
        if self.file_record.id is None:
            self.session.add(self.file_record)
        else:
            self.session.merge(self.file_record)
        self.session.commit()

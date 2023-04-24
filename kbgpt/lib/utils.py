import hashlib
from enum import Enum

import requests


def md5_url_content(url) -> str:
    """
    Get the MD5 hash of a URL's content
    """
    # Send a GET request to the URL
    response = requests.get(url, timeout=5)

    # Create an MD5 hash object
    md5_hash = hashlib.md5()

    # Update the hash with the content bytes
    md5_hash.update(response.content)

    # Get the hexadecimal representation of the hash
    hex_digest = md5_hash.hexdigest()

    return hex_digest


def md5_file_content(path) -> str:
    """
    Get the MD5 hash of a path's content
    """
    with open(path, "rb") as f:
        # Create an MD5 hash object
        md5_hash = hashlib.md5()

        # Update the hash with the content bytes
        md5_hash.update(f.read())

        # Get the hexadecimal representation of the hash
        hex_digest = md5_hash.hexdigest()

    return hex_digest


class ContentType(Enum):
    """
    create an enum for the different types of content:
    pdf, txt, html, url
    """

    PDF = "pdf"
    TEXT = "txt"
    HTML = "html"
    URL = "url"
    DOC = "doc"
    DOCX = "docx"

    @classmethod
    def get_content_type(cls, path):
        """
        Get the content type of a path
        """
        if path.startswith("http"):
            return ContentType.URL
        if path.endswith(".pdf"):
            return ContentType.PDF
        elif path.endswith(".txt"):
            return ContentType.TEXT
        elif path.endswith(".html") or path.endswith(".htm"):
            return ContentType.HTML
        elif path.endswith(".doc"):
            return ContentType.DOC
        elif path.endswith(".docx"):
            return ContentType.DOCX
        else:
            raise ValueError(f"path {path} not supported")

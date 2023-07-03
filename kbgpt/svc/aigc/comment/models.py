from enum import Enum

from pydantic import BaseModel


class RequestStep(Enum):
    """ steps to process the request """
    CLASSIFY = 1
    COMMENT = 2
    COMPLETE = 3


class Base(BaseModel):
    """ base class """
    step: str
    invoke_id: str
    post_id: str
    tokens: int
    cost: float


class Post(BaseModel):
    """model represents a post"""

    post_id: str
    title: str
    content: str


class Comment(Base):
    """model represents a comment"""

    comment: str


class Category(Base):
    """model class"""

    category: str
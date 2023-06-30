"""
doc string
"""
from typing import Any, Dict

from sqlalchemy import Column, Float, Integer, String, Text

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.db.mysql.base import OBase
from kbgpt.svc.models.comment import Category, Comment, Post


class VirtualCommentRecord(OBase, Base):
    """
    VirtualCommentRecord class
    """

    __tablename__ = "log_virtual_comment_record"

    type = Column(String(25, collation="utf8mb4_unicode_ci"))
    post_id = Column(Integer)
    content = Column(Text(collation="utf8mb4_unicode_ci"))
    result = Column(Text(collation="utf8mb4_unicode_ci"))
    tokens = Column(Integer)
    cost = Column(Float)


    def update_category(self, category: Category):
        """ update object for category """
        self.post_id = category.post_id
        self.type = category.step
        self.result = category.category
        self.tokens = category.tokens
        self.cost = category.cost
        self.invoke_id = category.invoke_id


    def update_comment(self, comment: Comment):
        """ update object for comment """
        self.post_id = comment.post_id
        self.type = comment.step
        self.result = comment.comment
        self.tokens = comment.tokens
        self.cost = comment.cost
        self.invoke_id = comment.invoke_id


    @classmethod
    def create(
        cls, kwargs: Dict = None, result: Any = None, seconds_spent: Float = 0.0
    ) -> "VirtualCommentRecord":
        """ create object """
        obj: VirtualCommentRecord = super().create(
            kwargs=kwargs, result=result, seconds_spent=seconds_spent
        )

        # pylint: disable=no-member
        if isinstance(result, Category):
            obj.update_category(result)
        elif isinstance(result, Comment):
            obj.update_comment(result)
        else:
            raise ValueError(f"no such type {result.__class__}")

        post: Post = kwargs["post"]
        obj.content = f"{post.title}\n{post.content}"
        return obj

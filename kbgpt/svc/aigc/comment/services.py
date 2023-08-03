"""
service to comment forum posts
"""
import asyncio
import logging
import re
from typing import List, Tuple
from uuid import uuid4

import openai
from sanic import Sanic

from config import profile
from kbgpt.lib.db.mysql.comment_record import VirtualCommentRecord
from kbgpt.lib.logging import alog
from kbgpt.lib.templates.engine import CommentEngine, SimpleEngine
from kbgpt.lib.templates.rendering.models import ModTemplateProvider, TemplateRepo
from kbgpt.lib.templates.rendering.repo.post_classification import CATEGORY_TO_IGNORE
from kbgpt.svc.aigc.comment.models import Category, Comment, Post, RequestStep
from kbgpt.svc.utils.openai import get_total_cost


class CommentAgent:
    """
    agent to give comment
    """

    def __init__(self, app: Sanic):
        self.lock = asyncio.Lock()
        self.log_list = []
        self.app = app
        self.temp_engine = CommentEngine(app.ctx.temp_repo)
        repo = TemplateRepo(ModTemplateProvider())
        self.class_engine = SimpleEngine(name="post_classification", tmp_repo=repo)

    @alog(VirtualCommentRecord)
    async def classify(self, post: Post, uid: str) -> Category:
        """classify the post"""
        completion = await self.class_engine.agenerate(
            title=post.title, content=post.content
        )
        usage = completion.usage
        total_tokens = usage.total_tokens
        cost = usage.cost
        category = completion.content

        return Category(
            post_id=post.post_id,
            step=RequestStep.CLASSIFY.name,
            category=category,
            tokens=total_tokens,
            cost=cost,
            invoke_id=uid,
        )

    @alog(VirtualCommentRecord)
    async def _get_the_comment(self, post: Post, uid: str) -> Comment:
        """get the comment"""
        completion = await self.temp_engine.agenerate(
            content=post.content, title=post.title
        )
        usage = completion.usage
        ans_content = completion.content
        total_tokens = usage.total_tokens
        cost = usage.cost
        logging.debug("get response from openai:")
        logging.debug(ans_content)
        sub_ans = re.split(r"\r?\n", ans_content)
        sub_ans = [re.sub(r"^\d+\.\s+", "", ans) for ans in sub_ans if ans]

        return Comment(
            post_id=post.post_id,
            step=RequestStep.COMMENT.name,
            comment=sub_ans[-1],
            cost=cost,
            tokens=total_tokens,
            invoke_id=uid,
        )

    async def get_one_comment(self, post: Post, uid: str) -> Comment:
        """get comment for the given post"""
        category = await self.classify(post, uid)
        logging.info("post classified as in category: %s", category)
        comment = None
        if category.category in CATEGORY_TO_IGNORE:
            comment = Comment(
                post_id=post.post_id,
                step=RequestStep.COMPLETE.name,
                comment=".",
                tokens=category.tokens,
                cost=category.cost,
                invoke_id=uid,
            )
        else:
            comment = await self._get_the_comment(post, uid)
            comment.tokens += category.tokens
            comment.cost += category.cost

        return comment

    def gen_chunk(
        self, list_of_posts: List[Post], chunk_size: int = 10
    ) -> List[Tuple[Post, str]]:
        """split list_of_posts in chunks of size chunk_size, yield it one at a time"""
        chunk = []
        for post in list_of_posts:
            tup = (post, str(uuid4()))
            chunk.append(tup)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        yield chunk

    async def __call__(self, list_of_posts: List[Post]) -> List[Comment]:
        """get comments for given all posts"""
        list_of_comments = []
        for chunk in self.gen_chunk(list_of_posts):
            requests = [self.get_one_comment(post, uid) for post, uid in chunk]
            chunk_of_comments = await asyncio.gather(*requests)
            list_of_comments.extend(chunk_of_comments)
        return list_of_comments

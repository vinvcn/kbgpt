"""
service to comment forum posts
"""

import asyncio
import logging
import re
from typing import List, Tuple

import openai
from pydantic import BaseModel
from uuid import uuid4

from config import profile
from kbgpt.lib.db.mysql.comment_record import VirtualCommentRecord
from kbgpt.svc.utils import get_total_cost
from kbgpt.lib.templates.post_classification import (
    CLASSFIER_TEMPLATE,
    CATEGORY_TO_IGNORE,
)
from kbgpt.lib.templates.comments import get_prompt_with_personality
from kbgpt.lib.db.mysql import Crud
from datetime import datetime


class Post(BaseModel):
    """model represents a post"""

    post_id: str
    title: str
    content: str


class Comment(BaseModel):
    """model represents a comment"""

    post_id: str
    comment: str
    tokens: int
    cost: float


class Category(BaseModel):
    """model class"""

    category: str
    tokens: int
    cost: float


class CommentAgent:
    """
    agent to give comment
    """

    def __init__(self):
        self.lock = asyncio.Lock()
        self.log_list = []

    async def append_to_log_list(self, log_entry: VirtualCommentRecord):
        async with self.lock:
            self.log_list.append(log_entry)

    async def classify(self, post: Post, uid: str) -> Category:
        """classify the post"""
        prompt = CLASSFIER_TEMPLATE.format(title=post.title, content=post.content)
        completion = await openai.ChatCompletion.acreate(
            model=profile.comment.generative_model,
            messages=[{"role": "user", "content": prompt}],
        )
        promp_tokens = completion["usage"]["prompt_tokens"]
        comp_tokens = completion["usage"]["completion_tokens"]
        total_tokens = completion["usage"]["total_tokens"]
        cost = get_total_cost(
            profile.comment.generative_model, promp_tokens, comp_tokens
        )
        category = completion.choices[0].message["content"]

        log_entry = VirtualCommentRecord()
        log_entry.invoke_id = uid
        log_entry.post_id = post.post_id
        log_entry.type = "classification"
        log_entry.success = True
        log_entry.content = prompt
        log_entry.result = category
        log_entry.tokens = total_tokens
        log_entry.timestamp = datetime.utcnow()
        log_entry.cost = cost

        await self.append_to_log_list(log_entry)
        return Category(category=category, tokens=total_tokens, cost=cost)

    async def _get_the_comment(self, post: Post, uid: str) -> Comment:
        """get the comment"""
        prompt = get_prompt_with_personality(content=post.content, title=post.title)
        logging.debug("submitting request to openai")
        completion = await openai.ChatCompletion.acreate(
            model=profile.comment.generative_model,
            messages=[{"role": "user", "content": prompt}],
        )
        ans_content = completion.choices[0].message["content"]
        promp_tokens = completion["usage"]["prompt_tokens"]
        comp_tokens = completion["usage"]["completion_tokens"]
        total_tokens = completion["usage"]["total_tokens"]
        cost = get_total_cost(
            profile.comment.generative_model, promp_tokens, comp_tokens
        )
        logging.debug("get response from openai:")
        logging.debug(ans_content)
        sub_ans = re.split(r"\r?\n", ans_content)
        sub_ans = [re.sub(r"^\d+\.\s+", "", ans) for ans in sub_ans if ans]

        log_entry = VirtualCommentRecord()
        log_entry.invoke_id = uid
        log_entry.type = "comment"
        log_entry.post_id = post.post_id
        log_entry.success = True
        log_entry.content = prompt
        log_entry.result = sub_ans[-1]
        log_entry.tokens = total_tokens
        log_entry.timestamp = datetime.utcnow()
        log_entry.cost = cost

        await self.append_to_log_list(log_entry)

        return Comment(
            post_id=post.post_id,
            comment=sub_ans[-1],
            cost=cost,
            tokens=total_tokens,
        )

    async def get_one_comment(self, post: Post, uid: str) -> Comment:
        """get comment for the given post"""
        category = await self.classify(post, uid)
        logging.info("post classified as in category: %s" % category)
        comment = None
        if category.category in CATEGORY_TO_IGNORE:
            comment = Comment(
                post_id=post.post_id,
                comment=".",
                tokens=category.tokens,
                cost=category.cost,
            )
        else:
            comment = await self._get_the_comment(post, uid)
            comment.tokens += category.tokens
            comment.cost += category.cost

        log_entry = VirtualCommentRecord()
        log_entry.invoke_id = uid
        log_entry.post_id = post.post_id
        log_entry.type = "request"
        log_entry.content = f"{post.title}\n\n{post.content}"
        log_entry.success = True
        log_entry.result = comment.comment
        log_entry.tokens = comment.tokens
        log_entry.timestamp = datetime.utcnow()
        log_entry.cost = comment.cost
        await self.append_to_log_list(log_entry)
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
        crud = Crud(profile.db_url)
        crud.create_session()
        crud.batch_insert(self.log_list)
        crud.close_session()

        return list_of_comments

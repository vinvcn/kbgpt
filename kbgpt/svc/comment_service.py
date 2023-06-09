"""
service to comment forum posts
"""

import asyncio
import logging
import re
from typing import List

import openai
from pydantic import BaseModel

from config import profile
from kbgpt.svc.utils import get_total_cost
from kbgpt.lib.templates.post_classification import CLASSFIER_TEMPLATE, CATEGORY_TO_IGNORE
from kbgpt.lib.templates.comments import get_prompt_with_personality



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

    def gen_chunk(self, list_of_posts: List[Post], chunk_size: int = 10) -> List[Post]:
        """split list_of_posts in chunks of size chunk_size, yield it one at a time"""
        chunk = []
        for post in list_of_posts:
            chunk.append(post)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        yield chunk

    async def classify(self, post: Post) -> Category:
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
        return Category(category=category, tokens=total_tokens, cost=cost)

    async def _get_the_comment(self, post: Post) -> Comment:
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
        return Comment(
            post_id=post.post_id, comment=sub_ans[-1], cost=cost, tokens=total_tokens
        )

    async def get_one_comment(self, post: Post) -> Comment:
        """get comment for the given post"""
        category = await self.classify(post)
        logging.info("post classified as in category: %s" % category)
        if category.category in CATEGORY_TO_IGNORE:
            return Comment(
                post_id=post.post_id,
                comment=".",
                tokens=category.tokens,
                cost=category.cost
            )
        else:
            comment = await self._get_the_comment(post)
            comment.tokens += category.tokens
            comment.cost += category.cost
            return comment


    async def __call__(self, list_of_posts: List[Post]) -> List[Comment]:
        """get comments for given all posts"""
        list_of_comments = []
        for chunk in self.gen_chunk(list_of_posts):
            requests = [self.get_one_comment(post) for post in chunk]
            chunk_of_comments = await asyncio.gather(*requests)
            list_of_comments.extend(chunk_of_comments)
        return list_of_comments

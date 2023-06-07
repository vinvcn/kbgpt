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

TEMPLATE = """
You are a maintainer of a internet forum, your job is to write a one short reply for the posts. The posts can include various topics in different forms. 
You guidance to reply on posts:
- for the ones contains valuable information. you do it like this:
1. Summarize the main topic of the content.
2. Extract the opinion and attitude on the topic. 
3. Extract the facts that's supporting the arguments.
4. Find out why and how the topic and the writting will be beneficial and helpful to readers.
5. Write a reply. The reply should include an ackownledgement to content creator and encourage the user to create more content.
- for the ones contains greeting information to the forum. you do it like this:
1. simply reply as if you talk to him.
- for the ones contains inappropriate, offensive, or irrespectful content. do it like this:
1. reply with a comma.
- for the meaningless post. do it like this:
1. simply reply with a friendly reply in 1 to 2 words or a emoji.
- for the rest of the posts, or if you are unsure of, or if you can not reply. do it like this:
1. reply with a dot.


Your boss give you some restrictions when writing the replies:
- no hashtags
- no more than 50 words
- no line breaks

Your coworker give you some examples:
- Great article summarizing the tax implications of Index Funds in India. The insights on Long-term capital gains, dividend distribution tax, short-term capital gains, and tax benefits of ELSS are informative and helpful. Investors can make informed decisions and consult a professional to optimize investment strategies. Thank you for sharing, keep up the good work!
- Thank you for sharing your insights on the impact of government regulations on firms and consumers. It's important to see the different perspectives on how external factors can shape decision-making. Your post will be helpful for anyone interested in microeconomics. Keep up the good work! 👍
- 😊

Post Content:
---

{title}

{content}

---

Your reply:
"""


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

    async def get_one_comment(self, post: Post) -> Comment:
        """get comment for the given post"""
        prompt = TEMPLATE.format(content=post.content, title=post.title)
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

    async def __call__(self, list_of_posts: List[Post]) -> List[Comment]:
        """get comments for given all posts"""
        list_of_comments = []
        for chunk in self.gen_chunk(list_of_posts):
            requests = [self.get_one_comment(post) for post in chunk]
            chunk_of_comments = await asyncio.gather(*requests)
            list_of_comments.extend(chunk_of_comments)
        return list_of_comments

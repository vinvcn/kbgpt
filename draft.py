import asyncio

from kbgpt.lib.llm.openai import Message, OpenAI
from kbgpt.lib.templates.rendering.repo.report_weekly import TEMPLATE


async def func():
    client = OpenAI()
    result = await client.chat_completion(
        model="gpt-3.5-turbo", messages=[Message(role="system", content=TEMPLATE)]
    )

    print(result.content)


asyncio.run(func())

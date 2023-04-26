"""
Cli module for kbgpt
"""
import asyncio

from kbgpt.svc.file_services import add_kb
from kbgpt.svc.qa_services import QAagent


def add_knowledge_base():
    """add knowledge base"""
    asyncio.run(add_kb())


def handle_qa():
    """
    Handle the QA mode"""
    agent = QAagent.get_instance()
    while True:
        question = input("Enter a question: ")
        response, _ = asyncio.run(agent.answer_question(question))
        print(response)


# def handle_qa():
#     """
#     Handle the QA mode"""

#     async def helper():
#         agent = await create_agent(streaming=True)
#         while True:
#             question = input("Enter a question: ")
#             response = await agent.acall({"question": question})
#             print(response)

#     asyncio.run(helper())

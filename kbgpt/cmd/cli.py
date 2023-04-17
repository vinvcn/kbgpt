import asyncio

from config import *
from kbgpt.svc.file_services import add_kb
from kbgpt.svc.qa_services import QAagent


def add_knowledge_base():
    """add knowledge base"""
    asyncio.run(add_kb())


def handle_qa():
    """
    Handle the QA mode"""
    agent = QAagent()
    while True:
        question = input("Enter a question: ")
        response = asyncio.run(agent.answer_question(question))
        print(response)

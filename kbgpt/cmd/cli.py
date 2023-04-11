from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import QAagent


def handle_file(path: str):
    """
    Handle the file mode"""
    add_file_to_customer_service(path)


def handle_qa():
    """
    Handle the QA mode"""
    agent = QAagent(1)
    while True:
        question = input("Enter a question: ")
        response = agent.answer_question(question)
        print(response)

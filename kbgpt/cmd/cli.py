from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import answer_question_as_a_customer_service_agent


def handle_file(path: str):
    """
    Handle the file mode"""
    add_file_to_customer_service(path)


def handle_qa():
    """
    Handle the QA mode"""
    while True:
        question = input("Enter a question: ")
        response = answer_question_as_a_customer_service_agent(question)
        print(response)

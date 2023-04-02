"""
main entry point to the application
"""
from langchain.document_loaders import BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def run():
    """
    run method
    """
    loader = BSHTMLLoader("/Users/admin/Downloads/Introduction – API Reference.html")
    data = loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200))
    print(data)
    
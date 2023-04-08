
"""
main entry point to the application
"""

import argparse
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import TextLoader

# Define the argument parser
parser = argparse.ArgumentParser()

# Add the command-line arguments
parser.add_argument('--persist-dir', type=str, help='directory to persist db')
parser.add_argument('--text-file', type=str, help='Execute command 1')

# Parse the arguments
args = parser.parse_args()

db_dir = args.persist_dir
text_file = args.text_file

if not text_file:
    print('No text file specified')
    parser.print_help()
    exit(1)

if not db_dir:
    print('No persist directory specified')
    parser.print_help()
    exit(1)

loader = TextLoader(text_file)
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
vectordb = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=db_dir)
vectordb.persist()


FROM    python:3.11.3
RUN     pip install poetry
RUN     pip install chromadb==0.3.21
RUN     poetry config virtualenvs.options.system-site-packages true
RUN     poetry config virtualenvs.create false
RUN     poetry install --no-dev



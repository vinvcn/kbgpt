## KBGPT

This project contains wraps the workflow engine with the Sanic Web Server.

The business logic for AIGC with ChatGPT can be complex and non-deterministic. The project attempts to use workflow engine to define the logic between may AIGC invocations.


### Workflow Engine

The code in `kbgpt/lib`.

Workflow engine wraps step in invoking LLMs into DAGs(Directed Acyclic Graphs). The steps can than read outputs from previous steps and building complex applications. Each step has it's own auxiliaries such as caching, logging and retry.

This code base comes with some frequently used steps - vector database, prompt engineering, Text To Speech, etc.

### Prompt Engineering

This project relies on Jinja2 templating to render templates and data into prompts.

### Web Service

Sanic Web Server was chosen, and Python Async IO was applied whenever possible to unblock the main thread.

### Development guide

docker-compose file is under `dockerfile`.

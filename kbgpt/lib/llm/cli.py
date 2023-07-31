import asyncio

import click

from .openai import OpenAI


@click.group(name="openai")
def cli():
    pass


@cli.command()
def list_models():
    llm = OpenAI()
    result = asyncio.run(llm.list_models())
    print(result)

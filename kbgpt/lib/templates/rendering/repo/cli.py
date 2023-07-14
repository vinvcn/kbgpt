import asyncio
import os

import click

from config import profile
from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.db.mysql.prompt_template import PromptTemplate
from kbgpt.lib.utils import load_yaml_config


@click.group("template")
def cli():
    pass


@cli.command
def sync():
    crud = Crud(profile.db_url)
    asyncio.run(crud.init(None))
    dir_path = os.path.join(os.path.dirname(__file__), ".repo")
    files = os.listdir(dir_path)
    templates = []

    for file in files:
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path) and file_path.endswith(".yaml"):
            print(file_path)
            dct = load_yaml_config(file_path)
            print(dct)
            templates.append(PromptTemplate(**dct["template"]))

    crud.batch_insert(templates)
    asyncio.run(crud.destroy(None))

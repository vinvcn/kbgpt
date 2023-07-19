import asyncio
import os

import click
from redis import Redis

from kbgpt.lib.templates.rendering.models import RedisTemplateKeyFactory, Template
from kbgpt.lib.utils import load_yaml_config


@click.group("template")
def cli():
    pass


def get_config():
    dct = load_yaml_config(os.path.join(os.path.dirname(__file__), "config.yaml"))
    return dct


def list_temp(dir_path) -> Template:
    # dir_path = os.path.join(os.path.dirname(__file__), ".repo")
    files = os.listdir(dir_path)

    for file in files:
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path) and file_path.endswith(".yaml"):
            dct = load_yaml_config(file_path)
            yield Template(**dct["template"])


@cli.command
@click.option(
    "--env",
    type=click.Choice(["LOCAL", "FAT", "PRE", "PRO"], case_sensitive=False),
    required=True,
)
def sync_redis(env: str):
    config = get_config()
    redis_config = config["config"]["redis"]
    repo_path = config["config"]["repo"]["template"]["path"]
    url = redis_config[env.lower()]

    print(f"redis url {url}")
    redis = Redis.from_url(url)
    key_builder = RedisTemplateKeyFactory()

    repo_path = os.path.join(os.path.dirname(__file__), repo_path)

    for tmp in list_temp(repo_path):
        redis.json().delete(key_builder(tmp.template_id))
        redis.json().set(key_builder(tmp.template_id), "$", tmp.json(exclude_none=True))
        click.echo(f"template {tmp.template_id} saved")

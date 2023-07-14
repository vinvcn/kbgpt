import click

from .app import run as runserver


@click.group(name="server")
def cli():
    pass


@cli.command()
def run():
    runserver()

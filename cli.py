"""
main entry point to the application
"""

import importlib
import os

import click

FOLDER_PATHS = ["kbgpt", "templates"]
FILE_NAME = "cli.py"


@click.group()
def cli():
    pass


def load_commands(extension_file):
    # Load commands from extension_file
    module = importlib.import_module(extension_file)
    cli.add_command(module.cli)


def find_files(folders, filename):
    """Find files recursively"""
    matches = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            for file in files:
                if file == filename:
                    matches.append(os.path.join(root, file))
    return matches


if __name__ == "__main__":
    result = find_files(FOLDER_PATHS, FILE_NAME)

    print(f"Found {len(result)} instances of CLIs in folder '{FOLDER_PATHS}':")
    for file_path in result:
        modname = file_path[: file_path.rfind(".")].replace("/", ".")
        print(f"loading module {modname}")
        load_commands(modname)

    cli()

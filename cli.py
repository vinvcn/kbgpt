"""
main entry point to the application
"""

import importlib
import os

import click

FOLDER_PATH = "kbgpt"
FILE_NAME = "cli.py"


@click.group()
def cli():
    pass


def load_commands(extension_file):
    # Load commands from extension_file
    module = importlib.import_module(extension_file)
    cli.add_command(module.cli)


def find_files(folder, filename):
    """Find files recursively"""
    matches = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file == filename:
                matches.append(os.path.join(root, file))
    return matches


if __name__ == "__main__":
    result = find_files(FOLDER_PATH, FILE_NAME)

    print(f"Found {len(result)} instances of CLIs in folder '{FOLDER_PATH}':")
    for file_path in result:
        modname = file_path[: file_path.rfind(".")].replace("/", ".")
        print(f"loading module {modname}")
        load_commands(modname)

    cli()

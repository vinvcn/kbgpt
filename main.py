"""
main entry point to the application
"""

import argparse

from config import *
from kbgpt.cmd.cli import handle_file, handle_qa
from kbgpt.web.app import run_debug

# Define the argument parser with top-level help
parser = argparse.ArgumentParser(description="Run the KBGPT application")
# add a subparser for the different subcommands: 1) server, 2) cli
subparsers = parser.add_subparsers(help="sub-command help", dest="command")
# add subparser for the server command
parser_server = subparsers.add_parser("server", help="run server mode")
parser_server = parser_server.add_argument("run", action="store_true", help="run server mode")
# add subparser for the cli command
parser_cli = subparsers.add_parser("cli", help="run cli mode")
# add flag to cli subparser and pass the path as a string
parser_cli.add_argument(
    "--path",
    type=str,
    help="path to the file",
)
# add flag to cli subparser indicting entering the qa mode
parser_cli.add_argument(
    "--qa",
    action="store_true",
    help="run qa mode",
)
args = parser.parse_args()
# handle the server subcommand
if args.command == "server":
    run_debug()
elif args.command == "cli":
    if args.qa:
        # handle the qa mode
        handle_qa()
    elif args.path is not None:
        # handle the file mode
        handle_file(args.path)
else:
    args.print_help()

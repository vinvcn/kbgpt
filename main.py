"""
main entry point to the application
"""

import argparse

from kbgpt.api.app import run

parser = argparse.ArgumentParser(description="Run the KBGPT application")
subparsers = parser.add_subparsers(help="sub-command help", dest="command")
parser_server = subparsers.add_parser("server", help="run server mode")
args = parser.parse_args()

if __name__ == "__main__":
    # handle the server subcommand
    if args.command == "server":
        run()
    else:
        args.print_help()

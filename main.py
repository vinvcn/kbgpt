"""
main entry point to the application
"""

import argparse

# Define the argument parser
parser = argparse.ArgumentParser()

# Add the command-line arguments
parser.add_argument('--split-cyb', action='store_true', help='Execute command 1')
parser.add_argument('--jinyong', action='store_true', help='Execute command 1')

# Parse the arguments
args = parser.parse_args()

# Execute the selected command
if args.split_cyb:
    from kbgpt import vectorize_cybrilla_doc
    vectorize_cybrilla_doc.run()
elif args.jinyong:
    from kbgpt import vectorize_jinyong
    vectorize_jinyong.run()
else:
    print('No command specified')
    parser.print_help()

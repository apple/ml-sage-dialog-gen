#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

import os
import json
import argparse
import re

def write_data(output_file, data):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=2)

def sorted_walk(top):
    # Get the root, directories, and files
    for root, dirs, files in os.walk(top):
        # Sort directories in alphabetical order
        dirs.sort()
        # Sort files in alphabetical order
        files.sort()
        # Yield the current root, directories, and files
        yield root, dirs, files


def create_json_entries(folder, output_file, neg_size=1):
    # Get absolute paths
    folder = os.path.abspath(folder)
    output_file = os.path.abspath(output_file)

    # Create list to store JSON entries
    entries = []

    # Iterate through files in the folder
    for root, _, files in sorted_walk(folder):
        for file in files:
            # Read contents of the file
            with open(os.path.join(root, file), 'r') as file:
                content = file.read()

            # Split the content into turns
            turns = content.split('\n')

            history = []
            i = 0
            while i < len(turns):
                if turns[i].startswith('🧑‍💻:'):
                    instruction = turns[i].strip('🧑‍💻: ')
                    pattern = r'\{[^}]*\}'
                    instruction = re.sub(pattern, '', instruction).lstrip()
                    i += 1
                    positive = None
                    negatives = []
                    while i < len(turns) and turns[i].startswith(('🤖','\t🤖')):
                        if turns[i].startswith('🤖✅:'):
                            positive = turns[i].strip('🤖✅: ')
                        elif turns[i].startswith('\t🤖❌:'):
                            negatives.append(turns[i].strip('\t🤖❌: '))
                        i += 1

                    if positive is not None:
                        for negative in negatives[:neg_size]:
                            # Create JSON entry
                            entry = {
                                "instruction": instruction,
                                "input": "",
                                "output": [positive, negative],
                                "history": history[:]
                            }
                            entries.append(entry)

                        history.append([instruction, positive])
                else:
                    i += 1

    # Write JSON entries to output file
    print(f"Total size: {len(entries)}")
    write_data(output_file, entries)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make JSON files from conversation files')
    parser.add_argument('--input', type=str, help='folder storing conversation files')
    parser.add_argument("--suffix", type=str, help='suffix')
    parser.add_argument("--neg_size", type=int, default=1, help='size of negatives')
    args = parser.parse_args()

    output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(args.input))), f"comparison_{args.suffix}.json")
    create_json_entries(args.input, output_file, args.neg_size)
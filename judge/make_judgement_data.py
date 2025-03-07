#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

import os
import json
import argparse

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


def create_json_entries(folder_A, folder_B, output_file, max_size=None):
    # Get absolute paths
    folder_A = os.path.abspath(folder_A)
    folder_B = os.path.abspath(folder_B)
    output_file = os.path.abspath(output_file)


    # Create dictionary to store JSON entries
    entries = []

    # Iterate through files in folder A
    for root, _, files in sorted_walk(folder_A):
        for file in files:
            # Check if corresponding file exists in folder B
            corresponding_file_B = os.path.join(folder_B, os.path.relpath(root, folder_A), file)
            if os.path.exists(corresponding_file_B):
                # Read contents of both files
                with open(os.path.join(root, file), 'r') as file_A, open(corresponding_file_B, 'r') as file_B:
                    content_A = file_A.read()
                    content_B = file_B.read()
                    instruction = ("You are given a transcript of dialogue between a user and an assistant. You need to judge which assistant is better as a social chatbot. A good chatbot should sound like a real human, being colloquial, humorous, funny, intriguing, sympathetic, natural and not overly verbose. Judge by only stating 'Dialog X is better', where X is either A or B. Do not provide rationale. For example,\n"
                    "Dialog A:\n"
                    "blabla\n\n"
                    "Dialog B:\n"
                    "blabla\n\n"
                    "Conclusion: Dialog X is better\n\n"
                    "Now do the following:\n"
                    "Dialog A:\n"
                    f"{content_A}\n"
                    "Dialog B:\n"
                    f"{content_B}\n"
                    "Conclusion:\n")
                    # print(instruction)
                # Create JSON entry
                entry = {"instruction": instruction,
                        "input": "",
                        "output": f"{file}"}
                entries.append(entry)
                if max_size is not None and len(entries)>=max_size:
                    break

    ## Write JSON entries to output file
    print(f"Total size: {len(entries)}")
    write_data(output_file, entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make judgement JSON files')
    ## TODO
    parser.add_argument('--A', type=str, help='folder store dialog A')
    parser.add_argument('--B', type=str, help='folder store dialog A')
    parser.add_argument('--rev', action='store_true', help='flip A and B')
    parser.add_argument("--max_annot_size", '-m', type=int, default=None)

    args = parser.parse_args()
    output_file = os.path.join(os.path.dirname(args.A), f"judgement_{os.path.basename(args.A)}_vs_{os.path.basename(args.B)}.json")
    if args.rev:
        args.A, args.B = args.B, args.A
        output_file = output_file[:-4] + f"rev.json"
    if args.max_annot_size is not None:
        output_file = output_file[:-4] + f"{args.max_annot_size}.json"
    create_json_entries(args.A, args.B, output_file, args.max_annot_size)


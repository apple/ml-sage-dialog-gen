import os
import json
import argparse
import random
import re

def convert_to_json(input_folder):
    good_list = []
    pattern = r'\{[^}]*\}'
    for filename in os.listdir(input_folder):
        if filename.endswith(".txt"):
            conversation = {"id": os.path.splitext(filename)[0], "conversations": []}
            with open(os.path.join(input_folder, filename), "r") as file:
                lines = file.readlines()
                for i in range(0, len(lines), 2):
                    human_line = lines[i].strip()
                    gpt_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

                    if human_line.startswith("🧑‍💻:"):
                        human_line = human_line[4:].strip()
                        conversation["conversations"].append({"from": "human", "value": re.sub(pattern, '', human_line).lstrip()})
                    if gpt_line.startswith("🤖:"):
                        gpt_line = gpt_line[3:].strip()
                        conversation["conversations"].append({"from": "gpt", "value": gpt_line})

            good_list.append(conversation)
    random.shuffle(good_list)
    with open(os.path.join(os.path.dirname(input_folder), os.path.basename(input_folder)+".json"), "w") as output_file:
        json.dump(good_list, output_file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert text files to JSON")
    parser.add_argument("--input", type=str, required=True, help="Input folder containing text files")
    args = parser.parse_args()
    convert_to_json(args.input)
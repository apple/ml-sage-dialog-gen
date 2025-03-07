#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

# Make cocktails
import json
import argparse
import os
import random
from tqdm import tqdm
import copy
def write_data(output_file, data):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=2)

def blend_data(all_data, blend_num=2):
    data_len = len(all_data)
    for item in tqdm(all_data, total=len(all_data), desc=f"Blending",
                             bar_format="{l_bar}{bar} | remaining: {remaining}"):
        cutoff = round(len(item['conversations'])//2)*2
        item['conversations'] = item['conversations'][:cutoff] # round to an even number

    new_data=copy.deepcopy(all_data)
    for item in new_data:
        for _ in range(blend_num):
            rand_idx = random.randint(0, data_len-1)
            item['conversations'] += all_data[rand_idx]['conversations']
    return new_data

def mix_json(input_folder, data_spec, output_file, blend = False):
    all_data = []
    json_files = [file for file in os.listdir(input_folder) if file in data_spec.keys()]
    for json_file in json_files:
        file_path = os.path.join(input_folder, json_file)
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)[:data_spec[json_file]['size']]  # take the top XXX samples
            except KeyError:
                print(f"Error: Key '{json_file}' not found in data_spec.")
                continue
            for item in tqdm(data, total=len(data), desc=f"Mixing {json_file}",
                             bar_format="{l_bar}{bar} | remaining: {remaining}"):
                skip_flag = False

                for turn_idx, turn in enumerate(item['conversations']):
                    if set(turn.keys()) != set(['from', 'value']):
                        print(f"Warning: additional key {set(turn.keys())-set(['from', 'value'])} in {item['id']} from {json_file}.")
                        skip_flag = True
                        break
                    if turn['from'] != ['human','gpt'][turn_idx % 2]:
                        print(f"Warning: start with gpt in {item['id']} from {json_file}.")
                        skip_flag = True
                        break

                    if turn['from'] == 'human':
                        pass
                    elif turn['from'] == 'gpt':
                        try:
                            turn['value'] = data_spec[json_file]['prompt'] + turn['value']
                        except KeyError:
                            print(f"Error: Key 'prompt' not found for '{json_file}' in data_spec.")
                            continue
                    else:
                        print(f"Warning: additional key {turn['from']} in {item['id']} from {json_file}.")
                        skip_flag = True
                        break
                if len(item['conversations']) == 0:
                    print(f"Warning: empty dialog in {item['id']} from {json_file}.")
                    skip_flag = True
                if not skip_flag:
                    all_data.append(item)
    random.shuffle(all_data)
    print(len(all_data))
    if blend:
        all_data = blend_data(all_data)
    write_data(output_file, all_data)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='mix JSON files')
    parser.add_argument('--input_folder', '-i', type=str, help='folder store json files')
    parser.add_argument('--config', '-c', type=str, default='data_spec.json', help='folder store json files')
    parser.add_argument('--output_file', '-o', default='mix.json', type=str, help='output file path')
    parser.add_argument('--blend', action='store_true', help='blend data source')
    args = parser.parse_args()
    data_spec = json.load(open(os.path.join(args.input_folder, args.config), 'r'))
    if not os.path.exists(os.path.join(args.input_folder, "output")):
        os.makedirs(os.path.join(args.input_folder, "output"))
    mix_json(args.input_folder, data_spec, os.path.join(args.input_folder, "output", args.output_file), args.blend)
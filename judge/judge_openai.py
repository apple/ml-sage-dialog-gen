#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

#!pip install retry requests concurrent
import json
from openai import OpenAI
import json
from retry import retry
import requests.exceptions
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser
import os
from tqdm import tqdm

client = None  # Initialize global client variable

def get_args():
    parser = ArgumentParser()
    parser.add_argument("--input_file", '-i', type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True, default="gpt-3.5-turbo")
    parser.add_argument("--max_annot_size", '-m', type=int, default=None)
    return parser.parse_args()

def setup_openai_api():
    global client
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def read_data(input_file):
    with open(input_file, 'r') as file:
        return json.load(file)

def write_data(output_file, data):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=2)

@retry(
    (
        Exception,
        requests.exceptions.ReadTimeout,
        requests.exceptions.HTTPError,
    ),
    tries=5,
    delay=0.5,
    backoff=0.5,
    max_delay=2,
)
def annotate(text):
    global client
    instruction = text
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": instruction}
        ],
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


            
def judge_conversations(conversations, annotated_ids, max_size):
    annotated_data = []
    if max_size is None:
        max_size = len(conversations)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(annotate_and_append, item) for item in conversations[:max_size] if item["output"] not in annotated_ids}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Annotating", 
                           bar_format="{l_bar}{bar} | remaining: {remaining}"):
            result = future.result()
            if result is not None and ("predict" in result.keys()) and ("output" in result.keys()):
                annotated_data.append({"label": result["output"], "predict": result["predict"]})
                
    return annotated_data             

def annotate_and_append(item):
    annot_item = item.copy()
    try:
        annot_item["predict"] = annotate(annot_item["instruction"])
    except Exception as e:
        print(f"Failed on {annot_item['output']}: {e}")
    return annot_item



def main():
    args = get_args()
    
    global model_name
    model_name = args.model_name

    setup_openai_api()

    if "gpt" not in model_name:
        global client
        client.base_url = "http://localhost:8000/v1"

    data = read_data(args.input_file)

    annotated_ids = set()
    annotated_data = []

    # Replace "/" with "_" in model name for the output file
    safe_model_name = model_name.replace("/", "_")
    output_file = args.input_file.replace('.json', f'.{safe_model_name}.json')
    
    if os.path.exists(output_file):
        annotated_data = read_data(output_file)
        annotated_ids = {item["label"] for item in annotated_data}
    
    annotated_items = judge_conversations(data, annotated_ids, args.max_annot_size)

    annotated_data += annotated_items
    annotated_data.sort(key=lambda conv: conv["label"])

    write_data(output_file, annotated_data)

if __name__ == "__main__":
    main()





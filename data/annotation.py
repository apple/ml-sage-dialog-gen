#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

#!pip install retry requests concurrent
import json
import openai
import ast
import json
from retry import retry
import requests.exceptions
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser
import os
from tqdm import tqdm

in_context_conv = {'id':'in_context_conv', 'conversations':[
      {
        "from": "human",
        "value": "Zombies need to be stronger. They are just a nuisance at the moment"
      },
      {
        "from": "gpt",
        "value": "All zombies now spawn with full diamond armor with protection 4 and a sharp 5 fire aspect 2 diamond sword, and also have strength 2."
      },
      {
        "from": "human",
        "value": "There would be a total of 0 players if that hapenned."
      },
      {
        "from": "gpt",
        "value": "Well, I guess that's good, since everyone's dying."
      }]}
in_context_conv_converted = {'id':'in_context_converted', 'conversations':[
      {
        "from": "human",
        "value": "{motivation: complaint, emotion: frustrated, topic: [zombies]} Zombies need to be stronger. Right now they are just a nuisance."
      },
      {
        "from": "gpt",
        "value": "{motivation: suggestion, emotion: null, topic: [video games, zombies, combat]} All zombies will now spawn wearing full diamond armor with Protection 4, equipped with a Sharpness 5 Fire Aspect 2 diamond sword, and they will also have Strength 2. Is this a better challenge?"
      },
      {
        "from": "human",
        "value": "{motivation: objection, emotion: concerned, topic: [minecraft, players]} If that were to happen, there would be a total of zero players."
      },
      {
        "from": "gpt",
        "value": "{motivation: joke, emotion: sarcastic, topic: [minecraft]} Well, I guess that's good, since everyone's dying."
      }]}


def get_args():
    parser = ArgumentParser()
    parser.add_argument("--input_file", '-i', type=str, required=True)
    parser.add_argument("--max_annot_size", '-m', type=int, default=None)
    return parser.parse_args()

def setup_openai_api():
    # TODO: Make sure to replace the API key
    openai.api_key = os.environ["OPENAI_API_KEY"]

def read_data(input_file):
    with open(input_file, 'r') as file:
        return json.load(file)

def write_data(output_file, data):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=2)

@retry(
    (
        openai.error.Timeout,
        requests.exceptions.ReadTimeout,
        openai.error.ServiceUnavailableError,
        openai.error.RateLimitError,
        openai.error.APIError,
        requests.exceptions.ReadTimeout,
        requests.exceptions.HTTPError,
    ),
    tries=5,
    delay=0.5,
    backoff=0.5,
    max_delay=2,
)
def annotate(text, model="gpt-3.5-turbo"):
    instruction = f'Identify the motivation, emotion, and topics of the user utterance by annotating the dialog. \
        In rare cases, if really cannot find appropriate motivation or emotion, put "motivation: null" or "emotion: null". \
        Meanwhile, make the utterance more readable. \
        For each utterance from "gpt", if it is not ending with a question, add a bridging question at the end to lead to the next user utterance if needed. \
        Make no change if there is no need for adding a question. \
        For example, \n \
        Input:\n \
        {in_context_conv["conversations"]}\n \
        output:\n \
        {json.dumps(in_context_conv_converted["conversations"], indent=0)}\n \
        Now do the following new input:\n \
        {text}\n \
        output:\n'
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": instruction}
        ],
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.8,
    )
    return ast.literal_eval(response.choices[0].message.content.strip())


def annotate_and_append(item):
    annot_item = item.copy()
    try:
        annot_item["conversations"] = annotate(item["conversations"])
    except:
        print(f"Failed on {annot_item['id']}")
        return None
    return annot_item

            
def annotate_conversations(conversations, annotated_ids, max_size):
    annotated_data = []
    if max_size is None:
        max_size = len(conversations)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(annotate_and_append, item) for item in conversations[:max_size] if item["id"] not in annotated_ids}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Annotating", 
                           bar_format="{l_bar}{bar} | remaining: {remaining}"):
            result = future.result()
            if result is not None:
                annotated_data.append(result)
                
    return annotated_data             

def reannotate(data):
    reannotated = []
    try:
        for item in tqdm(data, total=len(data), desc="Reannotating", 
                        bar_format="{l_bar}{bar} | remaining: {remaining}"):
            try:
                for turn in item['conversations']:
                    if turn['from'] == 'human':
                        index_of_annot = turn['value'].find('}')
                        user_intent = turn['value'][:index_of_annot + 1]
                        turn['value'] = turn['value'][index_of_annot + 2:]
                        user_intent = user_intent.replace("{motivation:", "{u_motivation:").replace("emotion:", "u_emotion:").replace("topic:", "u_topic:")
                    else:
                        turn['value'] = user_intent + " "+ turn['value'].replace("{motivation:", "{a_motivation:").replace("emotion:", "a_emotion:").replace("topic:", "a_topic:") 
                        user_intent = ""
                reannotated.append(item)
            except Exception as e:
                print(f"Error processing item {item.get('id', 'unknown')}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error during reannotation: {str(e)}")
    finally:
        return reannotated

def main():
    args = get_args()
    setup_openai_api()
    data = read_data(args.input_file)

    annotated_ids = set()
    annotated_data = []

    output_file = args.input_file.replace('.json', '_reannot.json')
    if os.path.exists(output_file):
        annotated_data = read_data(output_file)
        annotated_ids = {item["id"] for item in annotated_data}
    
    # Do annotation
    annotated_items = annotate_conversations(data, annotated_ids, args.max_annot_size)
    annotated_data += annotated_items
    annotated_data.sort(key=lambda conv: int(conv['id'].split('_')[-1]))
    
    # Do reannotation and save directly to final output
    reannotated_data = reannotate(annotated_data)
    if reannotated_data:
        write_data(output_file, reannotated_data)

if __name__ == "__main__":
    main()





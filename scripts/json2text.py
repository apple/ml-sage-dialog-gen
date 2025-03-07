import os
import json
import argparse

def convert_to_raw(input_json):
    """Convert JSON conversations to raw text format with emojis."""
    raw_conversations = []
    
    with open(input_json, 'r') as f:
        data = json.load(f)
    
    # Create output path by replacing .json with .txt
    output_file = os.path.splitext(input_json)[0] + '.txt'
    
    for conversation in data:
        raw_text = []
        
        for msg in conversation["conversations"]:
            if msg["from"] == "human":
                raw_text.append(f"🧑‍💻: {msg['value']}")
            elif msg["from"] == "gpt":
                raw_text.append(f"🤖: {msg['value']}")
        
        raw_conversations.append('\n'.join(raw_text))
    
    # Write all conversations to a single file in the same directory
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(raw_conversations))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSON to raw text format")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    args = parser.parse_args()
    convert_to_raw(args.input)
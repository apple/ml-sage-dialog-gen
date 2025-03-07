#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

import logging
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import re
import copy

LOGGER = logging.getLogger(__name__)

avatars: Dict[str, str] = {
    "user": "🧑‍💻",
    "assistant": "🤖",
}


def separate_state(dialog):
    state = copy.deepcopy(dialog)
    new_dialog = copy.deepcopy(dialog)
    pattern = r'(\{[^{}]+\})\s*'
    for i, turn in enumerate(dialog):
        if turn['from'] == 'gpt':
            res = re.split(pattern, turn['value'])
            state[i]['value'], new_dialog[i]['value'] = (" ".join(res[:-1])).lstrip().strip(), res[-1]
    return state, new_dialog

def merge_state(state, dialog):
    new_dialog = copy.deepcopy(dialog)
    for i, turn in enumerate(dialog):
        if turn['from'] == 'gpt':
            new_dialog[i]['value'] = state[i]['value'] + " " + turn['value'] 
    return new_dialog


def boolean_string(s):
    if s.lower() not in {"false", "true"}:
        raise ValueError("Not a valid boolean string")
    return s.lower() == "true"


def load_model(path):
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(path, use_fast=False)
    print("Tokenizer loaded.")
    model = AutoModelForCausalLM.from_pretrained(
        path, low_cpu_mem_usage=True, torch_dtype=torch.float16
    ).cuda()
    print("Model loaded.")
    # model.half().cuda()
    return model, tokenizer

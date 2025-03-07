#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

import argparse
import tqdm
from game import DialogGame
from src.llmtuner import ChatModel
import os
import logging
from dataclasses import dataclass, field
import transformers
import sys

LOGGER = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    input: str = field(default=None, metadata={"help": "Input file path"})
    suffix: str = field(default=None, metadata={"help": "suffix"})
    turns: int = field(default=10, metadata={"help": "Set the maximum number of turns for the game"})
    num_candidates: int = field(default=1, metadata={"help": "Number of assistant generation candidates"})
    assist_temp: float = field(default=0.95, metadata={"help": "Assistant temperature"})
    assist_topK: int = field(default=50, metadata={"help": "Assistant top_k"})
    boost: float = field(default=None, metadata={"help": "boost strength"})
    mode: str = field(default=None, metadata={"help": "Assistant optimization mode"})
    selector: str = field(default='gpt-3.5-turbo', metadata={"help": "Selector model"})
    num_sessions: int = field(default=1, metadata={"help": "Num of sessions"})
    user_model_path: str = field(default=None, metadata={"help": "Path to the user model"})
    assistant_model_path: str = field(default=None, metadata={"help": "Path to the assistant model"})
    template: str = field(default="mistral", metadata={"help": "Template name"})
    finetuning_type: str = field(default="full", metadata={"help": "Finetuning type"})
    infer_backend: str = field(default="vllm", metadata={"help": "Inference backend"})
    vllm_maxlen: int = field(default=2048, metadata={"help": "Max length for vllm"})
    repetition_penalty: float = field(default=1.1, metadata={"help": "Repetition penalty"})



def run_chat(args, item, user_model, assistant_model):
    assistant_kargs = {'num_candidates':args.num_candidates, 'assist_temp':args.assist_temp, 'assist_topK':args.assist_topK, 'boost':args.boost, 'selector':args.selector}
    game = DialogGame(
        item=item,
        user_model=user_model,
        assistant_model=assistant_model,
        num_turns=args.turns,
        mode=args.mode,
        assistant_kargs=assistant_kargs,
    )

    item_name = "_".join(item.split(" ")[:8])
    for s in tqdm.tqdm(
        range(args.num_sessions), desc=f"Playing {item_name} for {args.num_sessions} times"
    ):
        file_name = os.path.join(
            os.path.dirname(args.input),
            f"{args.suffix}",
            f"_session_{s}" if args.num_sessions > 1 else "",
            f"{item_name}.txt"
        )
        if not os.path.exists(file_name):
            game.game_play()
            game.save_session(file_name)
        else:
            LOGGER.info(
                f"Skipping {item_name}, session {s} because it was found in output dir"
            )

if __name__ == "__main__":
    parser = transformers.HfArgumentParser((ModelArguments,))
    args, remaining = parser.parse_args_into_dataclasses(return_remaining_strings=True)
    sys.argv = sys.argv[:1] + remaining

    with open(args.input, "r", encoding="utf-8") as f_input:
        item_list = [l.strip() for l in f_input.readlines()]

    # Initialize models with command line arguments
    base_args = {
        "model_name_or_path": None,
        "infer_backend": args.infer_backend if hasattr(args, 'infer_backend') else "vllm",
        "vllm_maxlen": args.vllm_maxlen if hasattr(args, 'vllm_maxlen') else 2048,
        "repetition_penalty": args.repetition_penalty if hasattr(args, 'repetition_penalty') else 1.1,
        "template": args.template if hasattr(args, 'template') else "mistral",
        "finetuning_type": args.finetuning_type if hasattr(args, 'finetuning_type') else "full"
    }
    
    # Initialize separate models for user and assistant

    user_args = base_args.copy()
    user_args['model_name_or_path'] = args.user_model_path
    user_model = ChatModel(user_args)
   

    assistant_args = base_args.copy()
    assistant_args['model_name_or_path'] = args.assistant_model_path
    if assistant_args['model_name_or_path']==user_args['model_name_or_path']:
        assistant_model = user_model
    else:
        assistant_model = ChatModel(assistant_args)

    
    for item in tqdm.tqdm(item_list, desc="Playing Games"):
        run_chat(args, item, user_model, assistant_model)


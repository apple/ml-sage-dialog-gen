## dialogue tree search

user_model=$fullmodel
user_model_path=${user_model}
assistant_model=$fullmodel
assistant_model_path=${assistant_model}
search_save_dir=search_traj

python self_play/dialog_sim.py  \
    --template mistral \
    --finetuning_type full \
    --input empatheticdialogues/test_sent.tsv \
    --suffix $search_save_dir \
    --turns 8 \
    --infer_backend vllm \
    --vllm_maxlen 2048 \
    --repetition_penalty 1.1 \
    --user_model_path $user_model_path \
    --assistant_model_path $assistant_model_path

# convert result to conversation without states
python self_play/convert_sim.py --input $search_save_dir
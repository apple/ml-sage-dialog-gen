# Convert text to json
python scripts/text2json.py --input $search_save_dir

### DPO
python judge/make_comparison_data.py --input $search_save_dir  --suffix comparison_data

basemodel="sage_m3"
dpomodel="sage_dpo"
cd LLaMA-Factory/
deepspeed --num_gpus 8 src/train_bash.py \
    --deepspeed ds_config.json \
    --stage dpo \
    --do_train \
    --model_name_or_path $basemodel \
    --dataset comparison_data \
    --template mistral \
    --finetuning_type lora \
    --lora_target q_proj,v_proj \
    --output_dir $loramodel \
    --overwrite_cache \
    --overwrite_output_dir \
    --cutoff_len 4096 \
    --per_device_train_batch_size 8 \
    --gradient_accumulation_steps 1 \
    --lr_scheduler_type cosine \
    --logging_steps 10 \
    --warmup_steps 20 \
    --save_steps 100 \
    --eval_steps 100 \
    --evaluation_strategy steps \
    --load_best_model_at_end \
    --learning_rate 1e-5 \
    --num_train_epochs 3.0 \
    --val_size 0.01 \
    --dpo_ftx 1.0 \
    --plot_loss \
    --bf16
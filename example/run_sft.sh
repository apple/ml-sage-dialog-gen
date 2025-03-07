basemodel="mistralai/Mixtral-8x7B-Instruct-v0.1"
loramodel="sage_m1_lora"
cd LLaMA-Factory/
deepspeed --num_gpus 8 src/train_bash.py \
    --deepspeed ../ds_config.json \
    --stage sft \
    --do_train \
    --model_name_or_path $basemodel \
    --dataset data_mix \
    --template mistral \
    --finetuning_type lora \
    --lora_target q_proj,v_proj \
    --output_dir $loramodel \
    --overwrite_cache \
    --overwrite_output_dir \
    --per_device_train_batch_size 32 \
    --gradient_accumulation_steps 1 \
    --lr_scheduler_type cosine \
    --logging_steps 10 \
    --save_steps 100 \
    --learning_rate 5e-5 \
    --num_train_epochs 3.0 \
    --plot_loss \
    --val_size 0.01 \
    --bf16 \
    --cutoff_len 2048

# Merge the model
fullmodel="sage_m1"
python src/export_model.py \
    --model_name_or_path $basemodel \
    --adapter_name_or_path $loramodel \
    --template mistral \
    --finetuning_type lora \
    --export_dir $fullmodel \
    --export_size 2 \
    --export_legacy_format False


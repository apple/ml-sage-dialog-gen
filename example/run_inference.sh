
cd LLaMA-Factory/
python src/cli_demo.py \
    --model_name_or_path $basemodel \
    --template llama2 \
    --finetuning_type lora \
    --adapter_name_or_path $loramodel 

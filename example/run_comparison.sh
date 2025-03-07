
baseline=Mixtral-8x7B-Instruct-v0.1
name=sage_dpo

python judge/make_judgement_data.py --A results/${baseline}_converted --B results/${name}_converted
python judge/make_judgement_data.py --rev --A results/${baseline}_converted --B results/${name}_converted

judge_model=mistralai/Mixtral-8x7B-Instruct-v0.1
safe_model_name=${judge_model//\//_}
python judge/judge_openai.py -i results/judgement_${baseline}_converted_vs_${name}_converted.json --model_name ${judge_model}
python judge/judge_openai.py -i results/judgement_${baseline}_converted_vs_${name}_converted.rev.json --model_name ${judge_model}
mkdir -p results/judgement_${baseline}_${name}_${safe_model_name}
mv results/*.${safe_model_name}.json results/judgement_${baseline}_${name}_${safe_model_name}

python judge/analysis.py --input results/judgement_${baseline}_${name}_${safe_model_name}
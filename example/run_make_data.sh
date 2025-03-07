# annotation
python data/annotation.py --input example/data1.json
python data/annotation.py --input example/data2.json

# Mix data
mkdir -p data_mix
mv example/data1_reannot.json data_mix/
mv example/data2_reannot.json data_mix/
cp example/data_spec.json data_mix/
python data/mix_data.py -i data_mix/ --blend

# Move to LLaMA-Factory/data
cp data_mix/output/mix.json LLaMA-Factory/data

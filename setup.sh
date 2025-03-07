conda create -y -q -n llm python=3.10
source /miniconda/etc/profile.d/conda.sh
conda init bash
conda activate llm

git clone --branch v0.6.2 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -r requirements.txt

pip install deepspeed==0.14.4
pip install vllm==0.3.3
pip install jieba==0.42.1
pip install rouge-chinese==1.16.0
pip install nltk==3.8.1
pip install pydantic==1.10.13
pip install openai==0.28
pip install retry==0.9.2
pip install gradio==4.21.0
pip install wandb==0.18.7
pip install transformers==4.47.1

pip install flash_attn==2.5.6
pip install torch==2.1.2 torchvision==0.16.2

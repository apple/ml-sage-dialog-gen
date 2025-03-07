# import json
import logging
import os
# import platform
# import random
import re
# from typing import List, Optional

# import anthropic
# import openai
# import openai.api_requestor
# import requests.exceptions
# import torch
# from anthropic import AI_PROMPT, HUMAN_PROMPT, Anthropic
# from langchain.schema import AIMessage, BaseMessage, HumanMessage
# from retry import retry
import copy
LOGGER = logging.getLogger(__name__)
from user_script.utils import avatars
from user_script.judge.judge_openai import setup_openai_api
# openai.api_requestor.TIMEOUT_SECS = 20
import openai
from retry import retry
import requests.exceptions



def annotate(text, assistant_kargs):
    instruction = text
    if "gpt" not in assistant_kargs['selector']:
        openai.api_base = "http://localhost:8000/v1"
    response = openai.ChatCompletion.create(
        model=assistant_kargs['selector'],
        messages=[
            {"role": "user", "content": instruction}
        ],
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.8,
    )
    resp = response.choices[0].message.content.strip()
    pattern = re.compile(r'Response (\d+) is') 
    match = re.match(pattern, resp)
    if match:
        prediction = int(match.group(1))
        if prediction > assistant_kargs['num_candidates'] or prediction<1:
            raise ValueError("Prediction out of candidate range")
    else:
        if "No good one" in resp:
            print(resp)
        raise ValueError("Failed to extract prediction from response.")
    return prediction - 1

def select_best_response(new_text_resps, dialog_history, assistant_kargs, mode=None):
    if mode is None:
        instruction = ("You are given a transcript of dialogue between a user and a companion chatbot. You need to judge which response is better."
                    "A good companion chatbot should have properties like being consistent, humorous, funny, interesting, sympathetic, informative, engaging, appropriate, respectful."
                    "It should find a way to keep the dialog going but not by asking unnatural questions or questions sounds like interrogation/test."
                    "The assistant should be aware that it is an AI and not a human."
                    "Judge by only stating 'Response X is better',")
    elif mode == "humor":
        instruction = ("You are given a transcript of dialogue between a user and a chatbot. You need to judge which response is more funny, humorous and interesting, while being appropriate."
                    "The assistant should be aware that it is an AI and not a human."
                    "Judge by only stating 'Response X is funnier',")
    else:
        raise NotImplementedError("This mode has not been implemented yet")


    instruction += ("where X is the response id. Do not provide rationale. Only provide the judgement. If no response is good, generate 'No good one'. For example,\n"
                    "Dialog context:\n"
                    "blabla\n\n"
                    "Response 1:\n"
                    "blabla\n\n"
                    "Response 2:\n"
                    "blabla\n\n"
                    "...\n\n"
                    "Conclusion:\n"
                    "blabla\n"
                    "Response X is better\n\n"
                    "Now do the following:\n"
                    "Dialog context:\n"
                    f"{dialog_history}\n\n")

    for id, resp in enumerate(new_text_resps):
        instruction += f"Response {id+1}:\n"
        instruction += f"{avatars['assistant']}: {resp}\n\n"
    instruction += "Conclusion:\n"
    prediction = annotate(instruction, assistant_kargs)
    # print(prediction)
    negs = [n for id, n in enumerate(new_text_resps) if id!=prediction]
    return new_text_resps[prediction], negs





class DialogGame:
    def __init__(
        self,
        item: str,
        user_model,
        assistant_model,
        num_turns: int = 20,
        mode: str = None,
        assistant_kargs={},
    ) -> None:
        self.item = item
        self.num_turns = num_turns
        self.mode = mode
        self.assistant_kargs = assistant_kargs
        if "gpt" in self.assistant_kargs['selector']:
            setup_openai_api()    
        self.messages = []
        self.user_model = user_model
        self.assistant_model = assistant_model
        self.user_profile = [{"role": "user", "content": "who are you?"},
                    {"role": "assistant", "content": "{user_motivation: null, user_emotion: neutral} {assistant_motivation: null, assistant_emotion: neutral} I am a real human and I know you are an AI. I say things very briefly."},
                    {"role": "user", "content": "How's it going?"}]


    def rm_state(self, messages, role):
        new_messages = copy.deepcopy(messages)
        pattern = r'\{[^}]*\}'
        for i, turn in enumerate(messages):
            if turn['role'] == role:
                new_messages[i]['content'] = re.sub(pattern, '', turn['content']).lstrip()
        return new_messages


    @retry(
        (
            openai.OpenAIError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.HTTPError,
            ValueError,
        ),
        tries=5,
        delay=0.5,
        backoff=0.5,
        max_delay=2,
    )


    def assistant(self, stream = False):
        new_messages = self.rm_state(self.messages, role="user")
        # assistant_profile = "I am Angelica, an engaging, consistent, sympathetic, humorous, appropriate, informative, adaptable and respectful AI virtual character. I show genuine interests in learning about you and assistant you. My creator is Jeremy Z."
        if self.mode is None:
            assistant_profile = "I am a humorous, funny, interesting, informative, sympathetic, appropriate and caring AI social chatbot. How's it going?"
            new_messages = [{"role": "user", "content": "Who are you?"}, 
                            {"role": "assistant", "content": "{user_motivation: null, user_emotion: neutral} {assistant_motivation: introduction, assistant_emotion: friendly} "+f"{assistant_profile}"}] + new_messages 
        elif self.mode == "humor":
            assistant_profile = "Ah, the eternal question! I'm your friendly neighborhood chatbot, your digital sidekick, your genie in the screen! So, what can I do for you today?"
            new_messages = [{"role": "user", "content": "Who are you?"}, 
                            {"role": "assistant", "content": "{user_motivation: null, user_emotion: neutral} {assistant_motivation: humor, assistant_emotion: lighthearted} "+f"{assistant_profile}"}] + new_messages 
        else:
            raise NotImplementedError("This mode has not been implemented yet")

        if stream:
            response = ""
            for new_text in self.assistant_model.stream_chat(new_messages):
                # print(new_text, end="", flush=True)
                response += new_text
        else:
            new_text = self.assistant_model.chat(new_messages, 
                                            num_return_sequences=self.assistant_kargs['num_candidates'],
                                            temperature=self.assistant_kargs['assist_temp'],
                                            top_k=self.assistant_kargs['assist_topK'],
                                            boost=self.assistant_kargs['boost'])
            if self.assistant_kargs['num_candidates'] == 1:
                response, neg_responses = new_text[0].response_text.lstrip(), []
            else:
                new_text_resps = [n.response_text.lstrip() for n in new_text]
                response, neg_responses = select_best_response(new_text_resps, self.dialog_history(), self.assistant_kargs, mode=self.mode)
        return response, neg_responses

    def add_intent(self, new_messages, id = 1):
        pattern = r"user_motivation:\s*([^,}]+)"
        matches = re.findall(pattern, self.messages[id]['content'])
        user_motivation_value = matches[0].strip() if matches else "null"

        pattern = r"user_emotion:\s*([^,}]+)"
        matches = re.findall(pattern, self.messages[id]['content'])
        user_emotion_value = matches[0].strip() if matches else "neutral"        
        assistant_intent = f'{{user_motivation: null, user_emotion: neutral}} {{assistant_motivation: {user_motivation_value}, assistant_emotion: {user_emotion_value}}} '
        new_messages[id+len(self.user_profile)-1]['content'] = assistant_intent + new_messages[id+len(self.user_profile)-1]['content']
        return
    
    def only_leave_first_question(self, text):
        rm_list = ('?', ':)', ':-)', ';)', ';-)', '<3', ':D', ':P')
        if text.endswith(rm_list): 
            for item in rm_list:
                index = text.find(item)
                if index != -1:
                    text = text[:index + len(item)]
        return text
    
    def remove_sentence_after_questions(self, text):
        rm_list = ('?', ':)', ':-)', ';)', ';-)', '<3', ':D', ':P')
        last_match = len(text)-1
        for pattern in rm_list:
            matches = re.finditer(r'[!.] ', text)
            if matches:
                positions = [match.start() for match in matches if match.start() < text.find(pattern)]
                if positions:
                    last_match = min(last_match, positions[-1])
        return text[:last_match+1]

    def flip_role(self, messages):
        for i, turn in enumerate(messages):
            if turn['role'] == 'assistant':
                turn['role'] = 'user'
            elif turn['role'] == 'user':
                turn['role'] = 'assistant'
            else:
                raise KeyError
        messages = self.user_profile + messages 
        return messages


    def user(self, stream = False, rm_question = True):
        new_messages = self.rm_state(self.messages, role="assistant")
        new_messages = self.flip_role(new_messages)
        self.add_intent(new_messages)
        if stream:
            response = ""
            for new_text in self.user_model.stream_chat(new_messages):
                response += new_text
        else:
            new_text = self.user_model.chat(new_messages)[0]
            response = new_text.response_text
        if rm_question:
            new_response = self.remove_sentence_after_questions(response.lstrip())
            new_response = self.only_leave_first_question(new_response)
            if new_response.lstrip().rstrip() != ".":
                response = new_response
        return response.lstrip()
    


    def dialog_history(self):
        history = ""
        for item in self.messages:
            # text = re.sub("{You are a sympathetic bot.}", "", item["content"])
            text = item["content"]
            history += f'{avatars[item["role"]]}: {text}\n'
        return history

    def full_dialog_history(self):
        history = ""
        for item in self.messages_full:
            if item["role"] == "user":
                history += f'{avatars[item["role"]]}: {item["content"]}\n'
            else:
                history += f'{avatars[item["role"]]}✅: {item["content"]["positive"]}\n'
                for neg in item["content"]["negative"]:
                    history += f'\t{avatars[item["role"]]}❌: {neg}\n'
        return history

    def game_play(self):
        self.messages = [{"role": "user", "content": self.item}]
        if self.assistant_kargs['num_candidates'] > 1:
            self.messages_full = [{"role": "user", "content": self.item}]
        for t in range(self.num_turns):
            response, neg_responses = self.assistant()
            self.messages.append({"role": "assistant", "content": response})
            if self.assistant_kargs['num_candidates'] > 1:
                assert(len(neg_responses) > 0)
                self.messages_full.append({"role": "assistant", "content": {'positive': response, 'negative': neg_responses}})
            if t!= self.num_turns-1:   
                response = self.user()
                self.messages.append({"role": "user", "content": response})
                if self.assistant_kargs['num_candidates'] > 1:
                    self.messages_full.append({"role": "user", "content": response})    



    def save_session(self, path):
        # Print the conversation
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as out_f:
            out_f.write(self.dialog_history())
        if self.assistant_kargs['num_candidates'] > 1:
            full_path = os.path.join(os.path.dirname(path), "full")
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            with open(os.path.join(full_path, os.path.basename(path)), "w") as full_out_f:
                full_out_f.write(self.full_dialog_history())



# Copyright 2026 Junjie Ye
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import json
import os
from utils.client import client
from utils.utils import get_feedback_tools
from utils.constraint_checker import DialogueConstraintChecker
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from copy import deepcopy
import traceback


def get_feedback(message, sample, checker: DialogueConstraintChecker):
    content = message.get("content") or ""
    tool_calls = message.get("tool_calls") or []
    is_final = (len(tool_calls) == 0)

    if_fb = checker.get_feedback_if(
        is_final=is_final,
        content=content,
        tool_calls=tool_calls,
    )

    if tool_calls:
        codes = json.loads(sample['codes'])
        if_args_fb = checker.get_feedback_tool_arguments(
            if_feedback=if_fb,
            tool_calls=tool_calls,
        )
        feedback = get_feedback_tools(if_args_fb, tool_calls, codes)
    else:
        feedback = list(if_fb)

    finish = (is_final and (len(feedback) == 0)) or (
        checker.round >= checker.max_round)
    return finish, feedback


def sample_process(sample, args):
    id = sample['id']
    messages = deepcopy(sample['messages'])
    tools = json.loads(sample['tools'])
    checker = DialogueConstraintChecker(
        sample=sample,
        max_turns=20,
        validators_dir=args.input_dir,
    )

    finish = False
    while not finish:
        times = 0
        while times < args.max_retries:
            try:
                responses = None
                responses = args.client.chat(messages=messages, tools=tools)
                if responses.get("choices", None) and len(responses["choices"]) > 0:
                    if responses["choices"][0].get("message", None):
                        tmp_message = responses["choices"][0]["message"]
                        messages.append(tmp_message.copy())

                        finish, feedback = get_feedback(
                            tmp_message, sample, checker)
                        messages.extend(deepcopy(feedback))
                        if finish:
                            return id, messages
                        break
            except Exception as e:
                if any(i in str(e) for i in ["contain inappropriate content", "The response was filtered due to the prompt triggering", "The request was rejected because it was considered high risk", "The text field in the ContentBlock object at messages.1.content.0 is blank"]):
                    return id, messages
                times += 1
                time.sleep(1 + random.random())
                if times == args.max_retries:
                    if responses:
                        print(id, json.dumps(
                            responses, ensure_ascii=False, indent=2), flush=True)
                    else:
                        print(id, json.dumps(
                            messages, ensure_ascii=False, indent=2), flush=True)
                    traceback.print_exc()
                    print(id, e, flush=True)
                    finish = True

    return id, None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True, choices=["GPT-5.2", "GPT-5.1", "OpenAI o3",
                        "Claude Opus 4.6", "Gemini 3 Pro", "Seed-2.0-Pro", "Qwen3.5-Plus", "DeepSeek-V3.2", "Kimi K2.5"])
    parser.add_argument('--user', type=str, default=None)
    parser.add_argument('--api_key', type=str, default=None)
    parser.add_argument('--base_url', type=str, default=None)
    parser.add_argument('--thinking', action='store_true')

    parser.add_argument('--input_dir', type=str, default='data')
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--repeat', type=int, default=3)

    parser.add_argument('--max_workers', type=int, default=4)
    parser.add_argument('--max_retries', type=int, default=15)
    parser.add_argument('--start_id', type=int, default=0)
    parser.add_argument('--end_id', type=int, default=-1)

    return parser.parse_args()


def main():
    args = parse_args()

    with open(os.path.join(args.input_dir, 'input_data.jsonl'), 'r', encoding='utf-8') as f:
        input_data = [json.loads(line) for line in f]

    data = [
        {**deepcopy(input_sample), "id": f"{input_sample['id']}_{i}"}
        for i in range(args.repeat)
        for input_sample in input_data
    ]

    if args.end_id == -1:
        args.end_id = len(data)
    data = data[min(args.start_id, args.end_id): min(args.end_id, len(data))]
    print(f"Total number of data: {len(data)}")

    os.makedirs(args.output_dir, exist_ok=True)
    args.output_file = os.path.join(args.output_dir, "response.jsonl")
    ids = []
    if os.path.exists(args.output_file):
        with open(args.output_file, "r") as f:
            ids = [json.loads(line)["id"] for line in f.readlines()]

    process_data = [item for item in data if item["id"] not in ids]
    if len(process_data) == 0:
        print(f"Done for Generation!")
        return

    if args.max_workers == -1:
        args.max_workers = len(process_data)

    args.client = client(model=args.model, user=args.user,
                         api_key=args.api_key, base_url=args.base_url, thinking=args.thinking)
    print(
        f"Generating responses for {args.model}, length={len(process_data)}!")

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(sample_process, sample, args)
                   for sample in process_data]
        for future in tqdm(as_completed(futures), total=len(futures)):
            id, messages = future.result()
            if messages:
                with open(args.output_file, "a") as f:
                    f.write(json.dumps(
                        {"id": id, "messages": messages}, ensure_ascii=False) + "\n")
                    f.flush()
    print(f"Done for Generation!")


if __name__ == '__main__':
    main()

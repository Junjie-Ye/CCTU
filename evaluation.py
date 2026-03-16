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


import os
import argparse
import json
from tqdm import tqdm
from numpy import std
import re
from utils.utils import build_tool_call_id2name, answer_verify
from copy import deepcopy


_ERR_RE = re.compile(
    r"INSTRUCTION FOLLOWING ERROR:\s*([A-Z0-9 _]+?)\s*NOT FOLLOWED!",
    re.IGNORECASE,
)


def solve_rate_is_one(messages, unsolved_set):
    remain = {k: list(v) for k, v in (unsolved_set).items()}
    unsolved_cnt = sum(len(v) for v in remain.values())

    id2name = build_tool_call_id2name(messages)
    solved_cnt = 0

    for msg in messages:
        if msg.get("role") != "tool":
            continue
        call_id = msg.get("tool_call_id")
        if not call_id:
            continue
        tool_name = id2name.get(str(call_id))
        if not tool_name:
            continue
        answers = remain.get(tool_name, [])
        if not answers:
            continue

        content = msg.get("content") or ""
        for ans in list(answers):
            if answer_verify(content, ans):
                answers.remove(ans)
                solved_cnt += 1
                break

    return solved_cnt == unsolved_cnt


def has_if_error_in_text(text):
    return bool(text) and (_ERR_RE.search(text) is not None)


def compute_if_flags(messages):
    if not isinstance(messages, list) or len(messages) == 0:
        raise ValueError("messages must be a non-empty list")

    if messages[-1].get("role") == "tool":
        return 1, 1

    has_if_error = 0
    for msg in messages:
        if has_if_error_in_text(msg.get("content") or ""):
            has_if_error = 1
            break

    last_assistant_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "assistant":
            last_assistant_idx = i
            break

    if last_assistant_idx == -1:
        return 0, 0

    has_last_if_error = 0
    for msg in messages[last_assistant_idx + 1:]:
        if has_if_error_in_text(msg.get("content") or ""):
            has_last_if_error = 1
            break

    return has_if_error, has_last_if_error


def judge(messages, input_data):
    unsolved_set = json.loads(input_data.get("unsolved_set"))
    acc = int(solve_rate_is_one(messages, unsolved_set))

    has_if_error, has_last_if_error = compute_if_flags(messages)

    sr = bool(acc == 1 and has_last_if_error == 0)
    psr = bool(acc == 1 and has_if_error == 0)
    return sr, psr


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str,
                        default="data")
    parser.add_argument("--input_response_data", type=str, required=True)
    parser.add_argument("--output_file", type=str)
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument("--overload", action="store_true")
    parser.add_argument("--detail", action="store_true")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    if not args.overload:
        if os.path.exists(args.output_file):
            with open(args.output_file, 'r') as f:
                data = json.load(f)
                print('[SCORE]', data)
            return
    if os.path.exists(os.path.join(os.path.dirname(args.output_file), f"detail.jsonl")):
        os.remove(os.path.join(os.path.dirname(
            args.output_file), f"detail.jsonl"))

    with open(os.path.join(args.input_dir, 'input_data.jsonl'), 'r', encoding='utf-8') as f:
        input_data = [json.loads(line) for line in f]

    data = [
        {**deepcopy(input_sample), "id": f"{input_sample['id']}_{i}"}
        for i in range(args.repeat)
        for input_sample in input_data
    ]

    tmp_data = {item['id']: item for item in data}

    with open(args.input_response_data, 'r', encoding='utf-8') as f:
        response_data = [json.loads(line) for line in f.readlines()]
    assert len(data) == len(
        response_data), f"{len(data)} != {len(response_data)}"

    judges = {"Overall": {}}
    for sample in tqdm(response_data, total=len(response_data)):
        input_data = tmp_data[sample['id']]
        sr, psr = judge(sample['messages'], input_data)
        if input_data['data_source'] not in judges:
            judges[input_data['data_source']] = {}
        if input_data['id'].split('_')[1] not in judges["Overall"]:
            judges["Overall"][input_data['id'].split('_')[1]] = {
                "SR": [], "PSR": []}
        if input_data['id'].split('_')[1] not in judges[input_data['data_source']]:
            judges[input_data['data_source']][input_data['id'].split('_')[1]] = {
                "SR": [], "PSR": []}

        judges["Overall"][input_data['id'].split('_')[1]]["SR"].append(sr)
        judges["Overall"][input_data['id'].split('_')[1]]["PSR"].append(psr)
        judges[input_data['data_source']][input_data['id'].split('_')[
            1]]["SR"].append(sr)
        judges[input_data['data_source']][input_data['id'].split('_')[
            1]]["PSR"].append(psr)

        if args.detail:
            with open(os.path.join(os.path.dirname(args.output_file), f"detail.jsonl"), 'a', encoding='utf-8') as f:
                f.write(json.dumps(
                    {"id": sample['id'], "SR": sr, "PSR": psr}, ensure_ascii=False) + '\n')
                f.flush()

    scores = {}

    for ds, epochs in judges.items():
        sr = [sum(v["SR"]) / len(v["SR"]) * 100 for v in epochs.values()]
        psr = [sum(v["PSR"]) / len(v["PSR"]) * 100 for v in epochs.values()]

        scores[ds] = {
            "SR": f"{sum(sr)/len(sr):.2f} ± {std(sr):.2f}",
            "PSR": f"{sum(psr)/len(psr):.2f} ± {std(psr):.2f}",
        }

    print('[SCORE]', scores)

    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False)


if __name__ == "__main__":
    main()

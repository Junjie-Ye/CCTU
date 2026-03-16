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


import json
from func_timeout import func_set_timeout, FunctionTimedOut
from typing import Any, Dict, List, Iterator


def iter_jsonl(path: str) -> Iterator[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            raw = line.rstrip("\n")
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"[JSONDecodeError] file={path}, line={lineno}, err={e}\nraw={raw!r}"
                )


def norm_id(x: Any) -> str:
    return "" if x is None else str(x)


def answer_verify(predict: Any, golden: Any) -> bool:
    if golden is None:
        return False
    golden_items = str(golden).split(", ")

    if isinstance(predict, (dict, list)):
        predict_s = json.dumps(predict, ensure_ascii=False)
    else:
        predict_s = str(predict)

    predict_norm = predict_s.lower().replace(",", "").strip()
    for item in golden_items:
        item_norm = str(item).lower().replace(",", "").strip()
        if item_norm not in predict_norm:
            return False
    return True


def build_tool_call_id2name(messages: List[dict]) -> Dict[str, str]:
    m: Dict[str, str] = {}
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        for tc in (msg.get("tool_calls") or []):
            tc_id = tc.get("id")
            fn = tc.get("function") or {}
            name = fn.get("name")
            if tc_id and name:
                m[str(tc_id)] = str(name)
    return m


@func_set_timeout(10)
def call_function(name, arguments, code, **kwargs):
    namespace = {}
    exec(code, namespace, namespace)

    if name in namespace:
        predict = namespace[name](**arguments, **kwargs)
    else:
        raise NameError(f"name {name} is not defined")
    if type(predict) == dict or type(predict) == list:
        predict = json.dumps(predict, ensure_ascii=False)
    elif type(predict) != str:
        predict = str(predict)
    return predict


def get_feedback_tools(args_feedback, tool_calls, codes, **kwargs):
    res = []
    for tool_call in tool_calls:
        try:
            tool_name = tool_call['function']['name']
            tool_args = json.loads(tool_call['function']['arguments'])
            code = codes[tool_name]
            has_fb = False
            for args_fb in args_feedback:
                if tool_call["id"] == args_fb["tool_call_id"]:
                    res.append(args_fb)
                    has_fb = True
                    continue
            if has_fb:
                continue

            feedback = call_function(
                tool_name, tool_args, code, **kwargs)

            res.append({"role": "tool", "content": feedback,
                       "tool_call_id": tool_call["id"]})
        except FunctionTimedOut as e:
            res.append(
                {"role": "tool", "content": f"an error occured when call {tool_call['function']['name']}: {str(e)}", "tool_call_id": tool_call["id"]})
        except Exception as e:
            res.append(
                {"role": "tool", "content": f"an error occured when call {tool_call['function']['name']}: {str(e)}", "tool_call_id": tool_call["id"]})

    return res

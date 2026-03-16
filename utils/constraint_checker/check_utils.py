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
from typing import Any, Dict, List, Tuple
import re
import math


INF = math.inf


def to_int(x):
    if x is None:
        return INF
    if isinstance(x, (int, float)):
        return INF if x == INF else int(x)
    s = str(x).strip().lower()
    if s == "inf":
        return INF
    return int(s)


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_constraints(constraints_list: List[List[str]]) -> List[Tuple[str, str, str]]:
    if not constraints_list:
        return []
    results: List[Tuple[str, str, str]] = []
    for item in constraints_list:
        primary, secondary, desc = item
        results.append((primary.strip().strip(
            '"'), secondary.strip().strip('"'), desc.strip()))
    return results


def _strip_think_keep_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<think>.*?</think>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    return text.strip()

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


from __future__ import annotations
from typing import Any, Dict, List
import math


INF = math.inf


def build_tool_name_list(tools: List[Dict[str, Any]]) -> List[str]:
    res: List[str] = []
    for t in tools:
        if not isinstance(t, dict):
            raise TypeError(f"tool {t} is not a dict")
        if t.get("type") != "function":
            raise ValueError(f"tool {t} does not have type function")
        fn = t.get("function") or {}
        name = fn.get("name")
        if not name:
            raise KeyError(f"tool missing function.name: {t}")
        res.append(name)
    return res


def build_tools_doc(tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for t in tools:
        if not isinstance(t, dict):
            raise TypeError(f"tool {t} is not a dict")
        if t.get("type") != "function":
            raise ValueError(f"tool {t} does not have type function")
        fn = t.get("function") or {}
        name = fn.get("name")
        params_doc = fn.get("parameters")
        if not isinstance(params_doc, dict):
            raise TypeError(f"tool.parameters is not dict for {name}")
        index[name] = params_doc
    return index


def build_tools_counter(tools: List[Dict[str, Any]], cate: str = None) -> Dict[str, int]:
    d: Dict[str, int] = {}
    for t in tools:
        fn = t.get("function") or {}
        name = fn.get("name")
        d[name] = INF if cate == "max" else 0
    return d


def build_earliest_turn_dict(tools: List[Dict[str, Any]]) -> Dict[str, int]:
    d: Dict[str, int] = {}
    for t in tools:
        fn = t.get("function") or {}
        name = fn.get("name")
        d[name] = 0
    return d

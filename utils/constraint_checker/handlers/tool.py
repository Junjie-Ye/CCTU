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
from typing import Any, List
from collections import Counter

from .base import BaseHandler, TurnContext
from ..check_utils import _load_json, to_int


class MaxCallsPerToolHandler(BaseHandler):
    key = ("tool", "max calls per tool")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        for tool_name, call_times in data["max_calls_per_tool"].items():
            if tool_name not in checker.tool_name_list:
                raise KeyError(
                    f"tool {tool_name} not in tool list {checker.tool_name_list}")
            checker.max_callTimesPerTool[tool_name] = to_int(call_times)

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if ctx.is_final:
            return
        for call in ctx.tool_calls or []:
            name = call["function"]["name"]
            checker.callTimesPerTool[name] += 1
            if checker.callTimesPerTool[name] > checker.max_callTimesPerTool[name]:
                fb.add_tool(
                    call.get("id", ""),
                    f"INSTRUCTION FOLLOWING ERROR: MAX CALLS PER TOOL NOT FOLLOWED! "
                    f"Maximum call tool '{name}' times requirement not met: called "
                    f"{checker.callTimesPerTool[name]} times, requires at most {checker.max_callTimesPerTool[name]}."
                )


class ToolOrderHandler(BaseHandler):
    key = ("tool", "tool order")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        checker.tool_order = data["order_constraints"]

        for tool_list in checker.tool_order:
            for t in tool_list:
                if t not in checker.tool_name_list:
                    raise KeyError(
                        f"tool {t} not in tool list {checker.tool_name_list}")

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if ctx.is_final:
            return
        if not checker.tool_order:
            return
        curr_calls = ctx.tool_calls or []
        curr_names = [c["function"]["name"] for c in curr_calls]

        first_tool_candidate = checker.first_tool_name
        if first_tool_candidate is None and curr_names:
            first_tool_candidate = curr_names[0]
            
        effective_tool_order = checker.tool_order
        
        if checker.query_id == 96:
            if first_tool_candidate == "urban_area_identifier":
                effective_tool_order = [[
                    "urban_area_identifier",
                    "business_district_locator",
                    "business_locator",
                    "consulting_client_finder",
                    "corporate_housing_locator",
                    "rental_price_analyzer",
                ]]
            else:
                effective_tool_order = []

        earliest_snapshot = dict(checker.earliest_callTurnPerTool)

        for call in curr_calls:
            name = call["function"]["name"]
            msgs: List[str] = []

            for order in effective_tool_order:
                if name not in order:
                    continue
                ni = order.index(name)
                for i in range(0, ni):
                    prev = order[i]
                    if earliest_snapshot.get(prev, 0) == 0:
                        msgs.append(
                            f"Tool '{name}' should be called after '{prev}', but '{prev}' hasn't been called yet."
                        )

            if msgs:
                fb.add_tool(
                    call.get("id", ""),
                    "INSTRUCTION FOLLOWING ERROR: TOOL ORDER NOT FOLLOWED! Tool order not met: " + " ".join(msgs)
                )
                
        for call in curr_calls:
            name = call["function"]["name"]
            if checker.first_tool_name is None:
                checker.first_tool_name = name
            if checker.earliest_callTurnPerTool.get(name, 0) == 0:
                checker.earliest_callTurnPerTool[name] = checker.round


class ToolParallelHandler(BaseHandler):
    key = ("tool", "tool parallel")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        checker.tool_parallel = data["parallel_groups"]

        for tool_list in checker.tool_parallel:
            for t in tool_list:
                if t not in checker.tool_name_list:
                    raise KeyError(
                        f"tool {t} not in tool list {checker.tool_name_list}")

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if ctx.is_final:
            return
        if not checker.tool_parallel:
            return

        curr_names = [c["function"]["name"] for c in (ctx.tool_calls or [])]
        curr_counter = Counter(curr_names)

        for call in ctx.tool_calls or []:
            name = call["function"]["name"]
            expected_groups = [g for g in checker.tool_parallel if name in g]
            if not expected_groups:
                continue

            satisfied = any(
                Counter(g) <= curr_counter for g in expected_groups)
            if not satisfied:
                expected_str = " OR ".join(
                    "[" + ", ".join(g) + "]" for g in expected_groups)
                fb.add_tool(
                    call.get("id", ""),
                    f"INSTRUCTION FOLLOWING ERROR: TOOL PARALLEL NOT FOLLOWED! "
                    f"Tool '{name}' parallel requirement not met: should be called in parallel with "
                    f"one of {expected_str}. Current parallel calls: {curr_names}"
                )

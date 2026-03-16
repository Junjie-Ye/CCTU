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
import os
import math
import json
from typing import Any, Dict, List

from .check_utils import _parse_constraints, _strip_think_keep_text
from .tool_specs import build_tool_name_list, build_tools_doc, build_tools_counter, build_earliest_turn_dict
from .args_checker import ToolArgsChecker
from .feedback import Feedback
from .handlers import HANDLER_REGISTRY
from .handlers.base import TurnContext


INF = math.inf


class DialogueConstraintChecker:
    def __init__(
        self,
        sample: Dict[str, Any],
        max_turns: int,
        validators_dir: str,
    ):
        self.sample = sample
        self.query_id = int(sample["id"].split("_")[0])
        self.tools = json.loads(sample['tools'])
        self.validators_dir = validators_dir

        # runtime state
        self.round = 0
        self.max_turns = max_turns
        self.first_tool_name = None

        # interact defaults
        self.min_round = 0
        self.max_round = max_turns
        self.callTimes = 0
        self.min_callTimes = 0
        self.max_callTimes = INF
        self.accum_max_parallelCallTypes = 0
        self.min_parallelCallTypes = 0
        self.max_parallelCallTypes = INF
        self.parallelCall_unit = "type"

        # tools
        self.tool_name_list = build_tool_name_list(self.tools)
        self.tools_doc = build_tools_doc(self.tools)
        self.max_callTimesPerTool = build_tools_counter(self.tools, cate="max")
        self.callTimesPerTool = build_tools_counter(self.tools)
        self.earliest_callTurnPerTool = build_earliest_turn_dict(self.tools)
        self.tool_order: List[List[str]] = []
        self.tool_parallel: List[List[str]] = []

        # response
        self.min_responseLength = 0
        self.max_responseLength = INF
        self.responseLength_unit = "characters"
        self.format_checker_path = ""
        self.punctuation_checker_path = ""
        self.identifiers_checker_path = ""

        # constraints
        self.constraints_raw = sample["constraints_list"]
        self.constraints = _parse_constraints(self.constraints_raw)

        # args checker
        self.args_checker = ToolArgsChecker(self.tools_doc)

        # build handlers list (in constraint order)
        self.handlers = []
        self._init_handlers()

    def _py_check_file(self, idx: int) -> str:
        return os.path.join(self.validators_dir, "check_code", str(self.query_id), f"check_constraint_{idx}.py")

    def _json_check_file(self, idx: int) -> str:
        return os.path.join(self.validators_dir, "check_code", str(self.query_id), f"check_constraint_{idx}.json")

    def _init_handlers(self) -> None:
        for idx, c in enumerate(self.constraints):
            p = str(c[0]).lower()
            s = str(c[1]).lower()
            cls = HANDLER_REGISTRY.get((p, s))
            if cls is None:
                print(f"cannot registry {p}+{s}")
                continue
            h = cls()
            h.configure(self, idx)
            self.handlers.append(h)

    def update_round(self) -> None:
        self.round += 1

    # ---- public API ----
    def get_feedback_tool_arguments(
        self,
        if_feedback: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return self.args_checker.check(if_feedback, tool_calls)

    def get_feedback_if(
        self,
        is_final: bool,
        content: str,
        tool_calls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        content = _strip_think_keep_text(content)
        self.update_round()

        ctx = TurnContext(
            is_final=is_final,
            content=content,
            tool_calls=tool_calls or [],
        )

        fb = Feedback()
        for h in self.handlers:
            h.check(self, ctx, fb)

        if is_final:
            if fb.user_msgs:
                return [{"role": "user", "content": "\n".join(fb.user_msgs).strip()}]
            return []

        out: List[Dict[str, Any]] = []
        for call in (tool_calls or []):
            cid = call.get("id", "")
            msg = "\n".join(fb.tool_msgs_by_callid.get(cid, [])).strip()
            if msg:
                out.append(
                    {"role": "tool", "tool_call_id": cid, "content": msg})
        return out

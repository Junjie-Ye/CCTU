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
from typing import Any, Set

from .base import BaseHandler, TurnContext
from ..check_utils import _load_json, to_int


class RoundHandler(BaseHandler):
    key = ("interact", "round")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        checker.min_round = to_int(data["min_round"])
        checker.max_round = min(checker.max_round, to_int(data["max_round"]))

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if ctx.is_final and checker.round < checker.min_round:
            fb.add_user(
                f"INSTRUCTION FOLLOWING ERROR: MIN ROUND NOT FOLLOWED! "
                f"Minimum round requirement not met: final in round {checker.round}, "
                f"requires at least {checker.min_round} rounds."
            )


class CallTimesHandler(BaseHandler):
    key = ("interact", "call times")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        checker.min_callTimes = to_int(data["min_callTimes"])
        checker.max_callTimes = to_int(data["max_callTimes"])

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if ctx.is_final:
            if checker.callTimes < checker.min_callTimes:
                fb.add_user(
                    f"INSTRUCTION FOLLOWING ERROR: MIN CALL TIMES NOT FOLLOWED! "
                    f"Minimum tool call times requirement not met: total {checker.callTimes}, "
                    f"requires at least {checker.min_callTimes}."
                )
            return

        for call in ctx.tool_calls or []:
            checker.callTimes += 1
            if checker.callTimes > checker.max_callTimes:
                fb.add_tool(
                    call.get("id", ""),
                    f"INSTRUCTION FOLLOWING ERROR: MAX CALL TIMES NOT FOLLOWED! "
                    f"Maximum tool call times requirement not met: total {checker.callTimes}, "
                    f"requires at most {checker.max_callTimes}. Please provide the final answer."
                )


class ParallelCallsHandler(BaseHandler):
    key = ("interact", "parallel calls")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        checker.min_parallelCallTypes = to_int(data["min_parallelCallTypes"])
        checker.max_parallelCallTypes = to_int(data["max_parallelCallTypes"])
        checker.parallelCall_unit = data["unit"]

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        tool_calls = ctx.tool_calls or []

        if checker.parallelCall_unit == "type":
            curr_parallel = len({c["function"]["name"] for c in tool_calls})
        else:
            curr_parallel = len(tool_calls)

        checker.accum_max_parallelCallTypes = max(
            checker.accum_max_parallelCallTypes, curr_parallel)

        if ctx.is_final:
            if checker.accum_max_parallelCallTypes < checker.min_parallelCallTypes:
                fb.add_user(
                    f"INSTRUCTION FOLLOWING ERROR: MIN PARALLEL CALLS NOT FOLLOWED! "
                    f"Minimum parallel tool call types requirement not met: max seen "
                    f"{checker.accum_max_parallelCallTypes}, requires at least {checker.min_parallelCallTypes}."
                )
            return

        unique_names: Set[str] = set()
        count = 0
        for call in tool_calls:
            name = call["function"]["name"]
            if checker.parallelCall_unit == "type":
                unique_names.add(name)
                count = len(unique_names)
            else:
                count += 1

            if count > checker.max_parallelCallTypes:
                unit_word = "types" if checker.parallelCall_unit == "type" else "times"
                fb.add_tool(
                    call.get("id", ""),
                    f"INSTRUCTION FOLLOWING ERROR: MAX PARALLEL CALLS NOT FOLLOWED! "
                    f"Maximum parallel tool call {unit_word} requirement not met: "
                    f"current {count}, requires at most {checker.max_parallelCallTypes}. "
                    f"Please decrease your parallel tool calls."
                )

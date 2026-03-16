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
from typing import Any, Dict, List, Optional, Set
import json

from .schema_validate import validate_param_value


class ToolArgsChecker:
    def __init__(self, tools_doc: Dict[str, Dict[str, Any]]):
        self.tools_doc = tools_doc

    def check(
        self,
        if_feedback: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        feedback_list: List[Dict[str, Any]] = []

        if_fb_call_ids: Set[str] = set()
        for fb in (if_feedback or []):
            if isinstance(fb, dict) and fb.get("tool_call_id"):
                if_fb_call_ids.add(fb["tool_call_id"])
                feedback_list.append({
                    "role": fb.get("role", "tool"),
                    "tool_call_id": fb["tool_call_id"],
                    "content": fb.get("content", "") or "",
                })

        if not tool_calls:
            return feedback_list

        for call in tool_calls:
            fn = call.get("function") or {}
            name = fn.get("name", "") or ""
            raw_args = fn.get("arguments", "") or ""
            call_id = call.get("id", "") or ""

            if not call_id or call_id in if_fb_call_ids:
                continue

            err: Optional[str] = None

            if name not in self.tools_doc:
                err = f"Failed to call tool '{name}' as it does not exist"
            else:
                tool_doc = self.tools_doc[name] or {}
                props: Dict[str, Any] = tool_doc.get("properties") or {}
                required: List[str] = tool_doc.get("required") or []
                tool_doc_keys = set(props.keys())

                # parse JSON args
                try:
                    args = json.loads(raw_args)
                    if not isinstance(args, dict):
                        err = (
                            f"Failed to call tool '{name}' due to invalid argument format: "
                            f"expected JSON object, got {type(args).__name__}"
                        )
                        args = {}
                except Exception as e:
                    err = f"Failed to call tool '{name}' due to invalid JSON arguments: {e}"
                    args = {}

                # required / extra
                if err is None:
                    args_keys = set(args.keys())
                    missing = [p for p in required if p not in args_keys]
                    if missing:
                        err = (
                            f"Failed to call tool '{name}' due to missing required argument(s): "
                            f"{', '.join(missing)}"
                        )

                if err is None:
                    args_keys = set(args.keys())
                    extra = sorted(args_keys - tool_doc_keys)
                    if extra:
                        err = (
                            f"Failed to call tool '{name}' due to extra argument(s): "
                            f"{', '.join(extra)}"
                        )

                # recursive schema validate
                if err is None:
                    all_errs: List[str] = []
                    for arg_name, arg_val in args.items():
                        sub_schema = props.get(arg_name)
                        if isinstance(sub_schema, dict):
                            errs = validate_param_value(
                                arg_name, arg_val, sub_schema)
                            all_errs.extend(errs)
                    if all_errs:
                        err = (
                            f"Failed to call tool '{name}' due to invalid argument(s): "
                            + "; ".join(all_errs)
                        )

            if err:
                content = f"INSTRUCTION FOLLOWING ERROR: TOOL ARGUMENTS NOT FOLLOWED! {err.strip()}"
                feedback_list.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                })

        return feedback_list

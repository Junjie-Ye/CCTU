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
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Feedback:
    user_msgs: List[str] = field(default_factory=list)
    tool_msgs_by_callid: Dict[str, List[str]] = field(default_factory=dict)

    def add_user(self, msg: str) -> None:
        msg = (msg or "").strip()
        if msg:
            self.user_msgs.append(msg)

    def add_tool(self, call_id: str, msg: str) -> None:
        call_id = (call_id or "").strip()
        msg = (msg or "").strip()
        if not call_id or not msg:
            return
        self.tool_msgs_by_callid.setdefault(call_id, []).append(msg)

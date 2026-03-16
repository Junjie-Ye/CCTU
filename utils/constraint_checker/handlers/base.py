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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


ConstraintKey = Tuple[str, str]


@dataclass
class TurnContext:
    is_final: bool
    content: str
    tool_calls: List[Dict[str, Any]]


class BaseHandler(ABC):
    key: ConstraintKey

    @abstractmethod
    def configure(self, checker: Any, idx: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        raise NotImplementedError

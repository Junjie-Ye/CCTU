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
from typing import Dict, Type

from .base import BaseHandler, ConstraintKey
from .interact import RoundHandler, CallTimesHandler, ParallelCallsHandler
from .tool import MaxCallsPerToolHandler, ToolOrderHandler, ToolParallelHandler
from .response import ResponseLengthHandler, ResponseFormatHandler, ResponsePunctuationHandler, ResponseIdentifiersHandler


HANDLER_REGISTRY: Dict[ConstraintKey, Type[BaseHandler]] = {
    ("resource", "interaction rounds"): RoundHandler,
    ("resource", "tool call count"): CallTimesHandler,
    ("behavior", "parallel calls count"): ParallelCallsHandler,

    ("resource", "specific tool call count"): MaxCallsPerToolHandler,
    ("behavior", "sequential dependencies"): ToolOrderHandler,
    ("behavior", "parallel dependencies"): ToolParallelHandler,

    ("response", "length"): ResponseLengthHandler,
    ("response", "format"): ResponseFormatHandler,
    ("response", "content_2"): ResponsePunctuationHandler,
    ("response", "content_1"): ResponseIdentifiersHandler,
}

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
from typing import Any

from .base import BaseHandler, TurnContext
from ..validator_loader import call_validator
from ..check_utils import _load_json, to_int


class ResponseLengthHandler(BaseHandler):
    key = ("response", "length")

    def configure(self, checker: Any, idx: int) -> None:
        data = _load_json(checker._json_check_file(idx))
        checker.min_responseLength = to_int(data["min_responseLength"])
        checker.max_responseLength = to_int(data["max_responseLength"])
        checker.responseLength_unit = data["unit"]

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if not ctx.is_final:
            return
        content = ctx.content or ""
        char_n = len(content)
        word_n = len(content.split())

        if checker.responseLength_unit == "characters":
            if char_n < checker.min_responseLength:
                fb.add_user(
                    f"INSTRUCTION FOLLOWING ERROR: MIN LENGTH NOT FOLLOWED! "
                    f"Response length (characters) too short: {char_n}, min is {checker.min_responseLength}."
                )
            elif char_n > checker.max_responseLength:
                fb.add_user(
                    f"INSTRUCTION FOLLOWING ERROR: MAX LENGTH NOT FOLLOWED! "
                    f"Response length (characters) too long: {char_n}, max is {checker.max_responseLength}."
                )
        elif checker.responseLength_unit == "words":
            if word_n < checker.min_responseLength:
                fb.add_user(
                    f"INSTRUCTION FOLLOWING ERROR: MIN LENGTH NOT FOLLOWED! "
                    f"Response length (words) too short: {word_n}, min is {checker.min_responseLength}."
                )
            elif word_n > checker.max_responseLength:
                fb.add_user(
                    f"INSTRUCTION FOLLOWING ERROR: MAX LENGTH NOT FOLLOWED! "
                    f"Response length (words) too long: {word_n}, max is {checker.max_responseLength}."
                )


class ResponseFormatHandler(BaseHandler):
    key = ("response", "format")

    def configure(self, checker: Any, idx: int) -> None:
        checker.format_checker_path = checker._py_check_file(idx)

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if not ctx.is_final or not checker.format_checker_path:
            return
        ok, msg = call_validator(
            checker.format_checker_path, "validate_format", ctx.content)
        if not ok:
            fb.add_user(
                f"INSTRUCTION FOLLOWING ERROR: FORMAT NOT FOLLOWED! {msg}")


class ResponsePunctuationHandler(BaseHandler):
    key = ("response", "punctuation")

    def configure(self, checker: Any, idx: int) -> None:
        checker.punctuation_checker_path = checker._py_check_file(idx)

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if not ctx.is_final or not checker.punctuation_checker_path:
            return
        ok, msg = call_validator(
            checker.punctuation_checker_path, "validate_punctuation", ctx.content)
        if not ok:
            fb.add_user(
                f"INSTRUCTION FOLLOWING ERROR: PUNCTUATION NOT FOLLOWED! {msg}")


class ResponseIdentifiersHandler(BaseHandler):
    key = ("response", "identifiers")

    def configure(self, checker: Any, idx: int) -> None:
        checker.identifiers_checker_path = checker._py_check_file(idx)

    def check(self, checker: Any, ctx: TurnContext, fb: Any) -> None:
        if not ctx.is_final or not checker.identifiers_checker_path:
            return
        ok, msg = call_validator(
            checker.identifiers_checker_path, "validate_identifiers", ctx.content)
        if not ok:
            fb.add_user(
                f"INSTRUCTION FOLLOWING ERROR: IDENTIFIERS NOT FOLLOWED! {msg}")

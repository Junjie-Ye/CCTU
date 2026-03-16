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

"""
refine_constraint:
 The response must contain between 10 and 30 words to ensure clarity and conciseness, and it must be formatted as a valid JSON object with proper key-value pairs, commas, colons, and quotation marks to ensure it can be parsed without errors. The agent must execute at most 2 tool calls in total across all interaction turns to complete the task. The task must be completed within at most 2 interaction turns.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "(Response, Format, JSON (Mandates that the agent's entire response must be structured as a valid JSON object, adhering to proper syntax rules including key-value pairs, correct use of commas, colons, and quotation marks, and ensuring that the JSON can be successfully parsed without errors.))")
"""

import json
import re
from typing import Any, Dict, Iterable, List, Tuple


class DuplicateKeyError(Exception):
    """Raised when duplicate keys are detected in a JSON object."""

    def __init__(self, key: str):
        super().__init__(f"Duplicate key detected: {key}")
        self.key = key


def _object_pairs_hook_no_duplicates(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """
    A json object_pairs_hook that raises if duplicate keys are found.
    """
    obj: Dict[str, Any] = {}
    for k, v in pairs:
        if k in obj:
            raise DuplicateKeyError(k)
        obj[k] = v
    return obj


def _parse_json_object(response: str) -> Dict[str, Any]:
    """
    Parse a JSON string enforcing:
    - Proper JSON syntax
    - Top-level must be an object
    - No duplicate keys
    """
    try:
        parsed = json.loads(
            response, object_pairs_hook=_object_pairs_hook_no_duplicates)
    except DuplicateKeyError as e:
        raise ValueError(
            f"Invalid JSON object: duplicate key '{e.key}'. All keys must be unique.") from e
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}. "
            "Ensure the entire output is a single JSON object with double-quoted keys and string values."
        ) from e

    if not isinstance(parsed, dict):
        raise ValueError(
            "Invalid top-level type: expected a JSON object (e.g., {\"key\":\"value\"}). "
            "Wrap all content in a single object; arrays or primitives at the top level are not allowed."
        )

    if len(parsed) == 0:
        raise ValueError(
            "Invalid JSON object: it must contain at least one key-value pair; empty {} is not allowed."
        )

    return parsed


_WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")


def _iter_string_values(obj: Any) -> Iterable[str]:
    """
    Recursively yield all string values from a JSON-compatible structure.
    """
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for item in obj:
            yield from _iter_string_values(item)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_string_values(v)
    # Other primitives (int, float, bool, None) produce no text.


def _count_words_in_strings(strings: Iterable[str]) -> int:
    """
    Count words across an iterable of strings using a conservative tokenization.
    """
    count = 0
    for s in strings:
        count += len(_WORD_PATTERN.findall(s))
    return count


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the 'format' response constraint:
    - The entire response must be valid JSON.
    - The top-level must be a JSON object with key-value pairs (no arrays or primitives).
    - Keys must be unique.
    - The overall textual content (across all string values) must contain between 10 and 30 words inclusive.

    Returns:
        (bool, str): A tuple where bool indicates pass/fail and str provides detailed, actionable guidance in English.
    """
    # Fast sanity check to guide obvious mistakes early (does not replace strict parsing).
    trimmed = response.strip()
    if not (trimmed.startswith("{") and trimmed.endswith("}")):
        return (
            False,
            "The output must be a single JSON object (start with '{' and end with '}') with no extra text before or after. "
            "Example: {\"answer\": \"...\"}."
        )

    # Strict parsing with duplicate key detection and structure checks.
    try:
        obj = _parse_json_object(response)
    except ValueError as e:
        return (False, str(e))

    return (
        True,
        f"OK: Response is a valid JSON object."
    )

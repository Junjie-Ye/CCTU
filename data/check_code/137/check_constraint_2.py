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
 You must use at most one call to the anatomy_facts_provider tool and at most one call to the anatomical_info_provider tool. Your response must be concise, contain at most 20 words, end with a period, and contain a valid JSON object with a key "answer" containing the final numerical result.

response_constraints_non_length:
- idx 2: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
- idx 3: ('Response', 'Format', '(Response, Format, The agent\'s final response must contain a valid JSON object with a key "answer" containing the final numerical result.)')
"""

from typing import Tuple, List, Optional
import json

# Helper: Extract candidate JSON object substrings by tracking balanced braces,
# respecting quoted strings and escapes.


def _extract_json_objects(text: str) -> List[str]:
    objs: List[str] = []
    depth = 0
    start: Optional[int] = None
    in_string = False
    escaped = False

    for i, ch in enumerate(text):
        if in_string:
            if ch == '\\' and not escaped:
                escaped = True
            elif ch == '"' and not escaped:
                in_string = False
            else:
                escaped = False
            continue

        if ch == '"':
            in_string = True
            escaped = False
            continue

        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    objs.append(text[start:i + 1])
                    start = None

    return objs


def _is_numeric_json_value(value) -> bool:
    # In Python, bool is a subclass of int; explicitly exclude booleans.
    return (isinstance(value, (int, float)) and not isinstance(value, bool))


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a valid JSON object with a key "answer"
    whose value is a numeric final result.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            'Response is empty. Include a valid JSON object like {"answer": 42} before the final period.'
        )

    candidates = _extract_json_objects(response)
    if not candidates:
        return (
            False,
            'No JSON object detected. Add one JSON object like {"answer": 42} (place the period after the JSON).'
        )

    parsed_any = False
    found_answer_key = False
    for snippet in candidates:
        try:
            data = json.loads(snippet)
            parsed_any = True
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict):
            if "answer" in data:
                found_answer_key = True
                value = data["answer"]
                if _is_numeric_json_value(value):
                    return (
                        True,
                        'Validation passed: found a valid JSON object with a numeric "answer".'
                    )
                else:
                    vtype = type(value).__name__
                    return (
                        False,
                        f'The "answer" value must be numeric (int or float), not {vtype}. '
                        'Example: {"answer": 42}.'
                    )

    if not parsed_any:
        return (
            False,
            'Found brace-enclosed text but none was valid JSON. Ensure proper JSON syntax with double quotes: {"answer": 42}.'
        )

    if not found_answer_key:
        return (
            False,
            'A JSON object was found, but it lacks the "answer" key. Include "answer" with a numeric value, e.g., {"answer": 42}.'
        )

    # Fallback generic failure (should not be reached due to earlier returns).
    return (
        False,
        'Format validation failed. Include one valid JSON object with numeric "answer", e.g., {"answer": 42}.'
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' (after any JSON content).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            'Response is empty. It must end with a period "." placed after the JSON object.'
        )

    trimmed = response.rstrip()
    if trimmed.endswith('.'):
        return (True, 'Validation passed: response ends with a period.')
    else:
        return (
            False,
            'The response must end with a period "." after the JSON object. Example: {"answer": 5}.'
        )

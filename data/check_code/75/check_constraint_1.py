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
 The tool `cultural_geography_locator` must be called before `local_band_finder`, `music_origin_identifier`, `choreographer_finder`, `entity_location_finder`, and `cultural_info_retriever`. The total number of interaction turns must be between 6 and 8 (inclusive). The `cultural_info_retriever` tool must be used at most 2 times. Your response must end with a period. Your response must be at least 50 words and at most 150 words. Additionally, your final response must contain a valid JSON object with a key "traditional_dance" containing the answer as its value.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
- idx 5: ('Response', 'Format', 'The final response must contain a valid JSON object with a key "traditional_dance" containing the answer as its value.')
"""

import json
from typing import Tuple, List, Tuple as TyTuple


def _find_json_objects(text: str) -> List[TyTuple[str, int, int]]:
    """
    Scan the text and return substrings that are candidate JSON objects.
    Uses brace matching while being aware of quoted strings and escapes.
    Returns list of tuples: (json_substring, start_index, end_index_exclusive).
    """
    objs: List[TyTuple[str, int, int]] = []
    in_str = False
    escape = False
    depth = 0
    start_idx = None

    for i, ch in enumerate(text):
        if in_str:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                if depth == 0:
                    start_idx = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start_idx is not None:
                        objs.append((text[start_idx:i + 1], start_idx, i + 1))
                        start_idx = None
    return objs


def _has_meaningful_string(value) -> bool:
    """
    Check if a value is a non-empty string with at least one non-whitespace character.
    """
    return isinstance(value, str) and len(value.strip()) > 0


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' as the final non-whitespace character.
    """
    if not isinstance(response, str) or len(response.strip()) == 0:
        return (False, "The response is empty. Provide a complete answer and ensure the final non-whitespace character is a period '.'.")

    trimmed = response.rstrip()
    if not trimmed.endswith('.'):
        return (False, "The response must end with a period '.'. Add exactly one period as the final character of the entire response (outside any JSON block). Example: ... }.")
    return (True, "OK")


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a valid JSON object with a key 'traditional_dance'.
    The JSON must be syntactically valid (parseable) and the key must exist with a meaningful value.
    """
    if not isinstance(response, str) or len(response.strip()) == 0:
        return (False, "The response is empty. Include a valid JSON object like: {\"traditional_dance\": \"<your answer>\"} somewhere in the response.")

    candidates = _find_json_objects(response)
    if not candidates:
        return (False, "No JSON object detected. Add a parseable JSON object containing the key \"traditional_dance\". Example: {\"traditional_dance\": \"Hula\"}")

    parse_errors = []
    for json_sub, _, _ in candidates:
        try:
            data = json.loads(json_sub)
        except json.JSONDecodeError as e:
            parse_errors.append(
                f"Failed to parse a candidate JSON object: {e.msg} at pos {e.pos}")
            continue

        if isinstance(data, dict):
            if "traditional_dance" not in data:
                parse_errors.append(
                    "A JSON object was found but is missing the required key \"traditional_dance\".")
                continue

            val = data.get("traditional_dance")
            if not _has_meaningful_string(val):
                return (False, "The key \"traditional_dance\" must have a non-empty string value. Provide a concise textual answer, e.g., {\"traditional_dance\": \"Hula\"}.")
            # Passed all checks
            return (True, "OK")
        else:
            parse_errors.append(
                "A JSON candidate was parsed but is not an object (must be a JSON object/dict).")

    # If we reach here, no valid JSON object satisfied the schema
    joined_errors = " ".join(
        parse_errors) if parse_errors else "No parseable JSON object found."
    return (False, f"{joined_errors} Ensure the response includes a valid JSON object with the key \"traditional_dance\" and a non-empty string value. Example: {{\"traditional_dance\": \"Hula\"}}")

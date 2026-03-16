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
 Your response must be derived by interacting with the provided tools, must not exceed 8 interaction rounds, must contain a valid JSON object containing the key 'reelected_candidate' with the candidate's name as the value, must ensure the natural language explanation ends with a period to ensure proper sentence closure, and must limit calls to the election_result_analyzer tool to a maximum of 3 times.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "Must contain a valid JSON object containing the key 'reelected_candidate' with the candidate's name as the value")
- idx 2: ('Response', 'Punctuation', 'The natural language explanation must end with a period (.) to ensure proper sentence closure.')
"""

import json
import re
from typing import List, Tuple, Optional


def _find_json_objects(text: str) -> List[Tuple[object, int, int, str]]:
    """
    Scan the text and extract balanced JSON object substrings.
    Returns a list of tuples: (parsed_obj, start_index, end_index, raw_json_str).
    This parser handles strings and escaped quotes to avoid premature brace matching.
    """
    results_raw: List[Tuple[str, int, int]] = []
    in_string = False
    escape = False
    depth = 0
    start_idx: Optional[int] = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                if depth == 0:
                    start_idx = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start_idx is not None:
                        results_raw.append(
                            (text[start_idx:i + 1], start_idx, i + 1))
                        start_idx = None

    results: List[Tuple[object, int, int, str]] = []
    for raw, a, b in results_raw:
        try:
            parsed = json.loads(raw)
            results.append((parsed, a, b, raw))
        except Exception:
            # Skip non-JSON or invalid JSON substrings
            continue
    return results


def _find_valid_candidate_json(text: str, key: str = "reelected_candidate") -> List[Tuple[dict, int, int, str]]:
    """
    Returns a list of (obj, start, end, raw) for JSON objects that:
      - are dicts
      - contain the given key
      - have a non-empty string value for that key
    """
    candidates: List[Tuple[dict, int, int, str]] = []
    for obj, a, b, raw in _find_json_objects(text):
        if isinstance(obj, dict) and key in obj:
            val = obj[key]
            if isinstance(val, str) and val.strip():
                candidates.append((obj, a, b, raw))
    return candidates


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a valid JSON object with key 'reelected_candidate'
    whose value is a non-empty string.

    Returns:
      - (True, message) if at least one such JSON object exists.
      - (False, message) with actionable guidance otherwise.
    """
    all_json = _find_json_objects(response)
    if not all_json:
        return (
            False,
            "No parsable JSON object was found in the response. Include a valid JSON object like "
            '{"reelected_candidate": "Full Name"} directly in the final answer.'
        )

    valid = _find_valid_candidate_json(response, key="reelected_candidate")
    if not valid:
        # Diagnose common issues
        # 1) JSON present but missing key or wrong type/value
        has_any_dict = any(isinstance(obj, dict) for obj, _, _, _ in all_json)
        if not has_any_dict:
            return (
                False,
                "JSON was found but none of the objects are JSON dictionaries. Ensure you include an object like "
                '{"reelected_candidate": "Full Name"} (an object with key-value pairs).'
            )

        # Check if any dict has the key with invalid value type
        dicts = [obj for obj, _, _, _ in all_json if isinstance(obj, dict)]
        has_key = any("reelected_candidate" in d for d in dicts)
        if not has_key:
            return (
                False,
                "A JSON object was found, but it does not contain the key 'reelected_candidate'. "
                "Add the key exactly as 'reelected_candidate' with a non-empty string value, e.g., "
                '{"reelected_candidate": "Full Name"}.'
            )

        wrong_type = any(
            "reelected_candidate" in d and not isinstance(
                d["reelected_candidate"], str)
            for d in dicts
        )
        if wrong_type:
            return (
                False,
                "The value of 'reelected_candidate' must be a string. Use a non-empty string like "
                '{"reelected_candidate": "Full Name"}.'
            )

        empty_val = any(
            "reelected_candidate" in d and isinstance(
                d["reelected_candidate"], str) and not d["reelected_candidate"].strip()
            for d in dicts
        )
        if empty_val:
            return (
                False,
                "The value of 'reelected_candidate' is an empty string. Provide a non-empty name string, e.g., "
                '{"reelected_candidate": "Full Name"}.'
            )

        # Fallback generic message
        return (
            False,
            "Include a valid JSON object containing the key 'reelected_candidate' with a non-empty string value, e.g., "
            '{"reelected_candidate": "Full Name"}.'
        )

    # Success; optionally warn if multiple occurrences exist
    if len(valid) > 1:
        return (
            True,
            "Valid: found at least one JSON object with key 'reelected_candidate' and a non-empty string value. "
            "Consider keeping only one such JSON object in the final answer to avoid ambiguity."
        )

    return (
        True,
        "Valid: found a JSON object with key 'reelected_candidate' and a non-empty string value."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the natural language explanation after the JSON ends with a period.
    Rules enforced:
      - There must be at least one valid JSON object (as defined in validate_format).
      - There must be some explanatory text after the closing brace of the last valid JSON object.
      - The final non-whitespace character of the entire response must be a period (.).

    Returns:
      - (True, message) if all conditions are met.
      - (False, message) with actionable guidance otherwise.
    """
    valid_jsons = _find_valid_candidate_json(
        response, key="reelected_candidate")
    if not valid_jsons:
        return (
            False,
            "No valid JSON object with key 'reelected_candidate' was found, so punctuation cannot be validated. "
            "First include the JSON object, then append an explanation ending with a period."
        )

    # Use the last valid JSON as the anchor for the explanation
    _, _, end_idx, _ = max(valid_jsons, key=lambda t: t[2])

    trailing = response[end_idx:].strip()
    if not trailing:
        return (
            False,
            "Add a natural-language explanation after the JSON object, and ensure it ends with a period (.). "
            'Example: {"reelected_candidate": "Full Name"}, followed by "Full Name was reelected for a fourth term."'
        )

    # Ensure the final non-whitespace character of the entire response is a period
    final_char = None
    stripped = response.rstrip()
    if stripped:
        final_char = stripped[-1]

    if final_char != '.':
        return (
            False,
            "The final non-whitespace character of the entire response must be a period (.). "
            "Append or modify the explanation so that it ends with a single period and no additional content afterward."
        )

    return (
        True,
        "Valid: the explanation after the JSON is present and the final character is a period."
    )

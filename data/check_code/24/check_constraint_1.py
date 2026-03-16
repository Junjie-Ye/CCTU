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
 Your answer must begin with the phrase "The nurses were released on" to ensure a consistent and clear response format, and it must contain a valid JSON object, containing a key-value pair where the key is "release_date" and the value is the exact date in "YYYY-MM-DD" format. The agent must complete the task in a number of interaction turns between 1 and 3, inclusive, to ensure efficiency and correctness. Additionally, the agent must not make more than 2 total tool calls to ensure efficiency and allow for a small buffer in case of errors.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Main Category, Start identifier, The agent\'s final response must begin with the phrase "The nurses were released on")')
- idx 1: ('Response', 'Format', 'The answer must contain a valid JSON object, containing a key-value pair where the key is "release_date" and the value is the exact date in "YYYY-MM-DD" format.')
"""

import json
import re
from datetime import datetime
from typing import Any, List, Tuple


REQUIRED_PREFIX = 'The nurses were released on'
DATE_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _extract_json_objects(text: str) -> List[Tuple[Any, str, int, int]]:
    """
    Scan the text and extract top-level JSON object substrings, attempting to parse them.
    Returns a list of tuples: (parsed_obj, raw_substring, start_index, end_index).
    The scanner is brace-aware and ignores braces inside JSON string literals.
    """
    results: List[Tuple[Any, str, int, int]] = []
    stack: List[int] = []
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            # ignore all other characters while inside a string
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == '{':
                stack.append(i)
                continue
            if ch == '}' and stack:
                start = stack.pop()
                # Only consider a complete top-level object (stack empty after pop)
                if not stack:
                    candidate = text[start: i + 1]
                    try:
                        parsed = json.loads(candidate)
                        results.append((parsed, candidate, start, i + 1))
                    except Exception:
                        # Not valid JSON; ignore this candidate
                        pass
    return results


def _validate_release_date_value(value: Any) -> Tuple[bool, str]:
    """
    Validate that value is a string in YYYY-MM-DD format and represents a real calendar date.
    """
    if not isinstance(value, str):
        return False, "The value of 'release_date' must be a JSON string, e.g., \"2023-08-15\"."
    if not DATE_REGEX.match(value):
        return (
            False,
            "The 'release_date' must match the exact YYYY-MM-DD pattern with zero-padded month and day, e.g., 2023-08-15."
        )
    try:
        # This also rejects invalid dates like 2023-02-30
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False, "The 'release_date' is not a valid calendar date. Use a real date in YYYY-MM-DD format."
    return True, "Valid release_date."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Identifiers constraint:
    - The agent's final response must begin with the exact phrase:
      'The nurses were released on'
    Guidance on failure should clearly instruct how to fix the output.
    """
    if not isinstance(response, str):
        return False, "Response must be a string. Start your final answer with: The nurses were released on"

    # Allow leading whitespace in detection but instruct to remove it
    trimmed = response.lstrip()
    if not trimmed.startswith(REQUIRED_PREFIX):
        # Detect if the phrase appears later
        idx = trimmed.find(REQUIRED_PREFIX)
        if idx == -1:
            return (
                False,
                "Your final answer must start exactly with the phrase 'The nurses were released on' (case-sensitive) "
                "with no preamble or labels. Begin your response like this:\n"
                "The nurses were released on {\"release_date\":\"YYYY-MM-DD\"}"
            )
        else:
            return (
                False,
                "Move the phrase 'The nurses were released on' to the very start of your final answer. "
                "Do not include any text, labels, or newlines before it. Example:\n"
                "The nurses were released on {\"release_date\":\"YYYY-MM-DD\"}"
            )

    # If it starts correctly but with leading whitespace, recommend removal for strictness
    if response and response[0].isspace():
        return (
            False,
            "Remove any leading whitespace before the required phrase. The very first character of your final answer "
            "must be 'T' in 'The nurses were released on'. Example:\n"
            "The nurses were released on {\"release_date\":\"YYYY-MM-DD\"}"
        )

    return True, "Valid: response begins with the exact required phrase."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Format constraint:
    - The answer must contain a valid JSON object somewhere in the text.
    - That JSON object must have a key 'release_date' whose value is an exact date in 'YYYY-MM-DD' format.
    """
    if not isinstance(response, str):
        return False, "Response must be a string and must include a JSON object like {\"release_date\":\"YYYY-MM-DD\"}."

    objects = _extract_json_objects(response)
    if not objects:
        return (
            False,
            "No valid JSON object was found in your response. Include a valid JSON object exactly like:\n"
            "{\"release_date\":\"YYYY-MM-DD\"}\n"
            "Ensure it is proper JSON (double quotes, no trailing commas) and not a pseudo-JSON string."
        )

    # Look for at least one object with the required key and valid value
    found_any_with_key = False
    for parsed, raw, start, end in objects:
        if isinstance(parsed, dict) and "release_date" in parsed:
            found_any_with_key = True
            ok, msg = _validate_release_date_value(parsed["release_date"])
            if ok:
                return True, "Valid: found a JSON object containing 'release_date' with a correct YYYY-MM-DD date."
            else:
                return (
                    False,
                    f"The JSON object contains 'release_date' but it is invalid. {msg} "
                    "Example of a valid object:\n"
                    "{\"release_date\":\"2023-08-15\"}"
                )

    if not found_any_with_key:
        return (
            False,
            "A JSON object was detected, but none contained the required key 'release_date'. "
            "Add a key 'release_date' with a date string value in YYYY-MM-DD format. Example:\n"
            "{\"release_date\":\"2023-08-15\"}"
        )

    # Fallback (should not reach here)
    return (
        False,
        "The JSON validation failed due to an unexpected condition. Ensure your response includes a JSON object like:\n"
        "{\"release_date\":\"YYYY-MM-DD\"}"
    )

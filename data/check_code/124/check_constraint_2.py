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
 The answer must be concise, contain at most 10 words, contain a valid JSON object with a single key-value pair, where the key is "days" and the value is an integer indicating the number of days. Additionally, during the solution process, there must be at least one interaction turn in which the agent invokes at least two unique tool types simultaneously. The response must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'The answer must contain a valid JSON object with a single key-value pair, where the key is "days" and the value is an integer indicating the number of days.')
- idx 2: ('Response', 'Punctuation', '(Response, Punctuation, The response must end with a period to ensure proper sentence closure.)')
"""

import json
from typing import Tuple, Optional

# Helper: Extract the first top-level JSON object substring from a response.


def _extract_first_json_object(s: str) -> Optional[str]:
    in_string = False
    string_quote = None
    escape = False
    brace_count = 0
    start_idx = None

    for i, ch in enumerate(s):
        if in_string:
            if escape:
                escape = False
            else:
                if ch == '\\':
                    escape = True
                elif ch == string_quote:
                    in_string = False
                    string_quote = None
        else:
            if ch in ('"', "'"):
                in_string = True
                string_quote = ch
            elif ch == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif ch == '}':
                if brace_count > 0:
                    brace_count -= 1
                    if brace_count == 0 and start_idx is not None:
                        return s[start_idx:i + 1]
    return None


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a valid JSON object with exactly one key-value pair:
    the sole key must be "days" and its value must be an integer.
    """
    json_str = _extract_first_json_object(response)
    if json_str is None:
        return (
            False,
            'No JSON object found. Include exactly one JSON object formatted like {"days": <integer>} (e.g., {"days": 3}). '
            'Use double quotes around the key, avoid extra keys, and place only an integer as the value (no strings or floats).'
        )
    try:
        obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        return (
            False,
            'Braces detected but content is not valid JSON. Ensure proper JSON syntax with double-quoted key "days" and an integer value, '
            'e.g., {"days": 3}. Error: ' + str(e)
        )

    if not isinstance(obj, dict):
        return (
            False,
            'The extracted JSON must be an object (curly braces). Use {"days": <integer>}, not an array or string.'
        )

    if len(obj) != 1:
        return (
            False,
            'The JSON object must contain exactly one key-value pair. Remove any extra keys so it is exactly {"days": <integer>}.'
        )

    if "days" not in obj:
        return (
            False,
            'The sole key must be "days". Rename the key to exactly "days" (lowercase, no spaces), e.g., {"days": 3}.'
        )

    value = obj["days"]
    if type(value) is not int:
        return (
            False,
            'The "days" value must be an integer (e.g., 3), not a string ("3"), float (3.0), or boolean. '
            'Use {"days": 3}.'
        )

    return (
        True,
        'Format constraint satisfied: found a valid JSON object with single key "days" and an integer value.'
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    Ignores trailing whitespace when checking the final character.
    """
    stripped = response.rstrip()
    if not stripped:
        return (
            False,
            'The response is empty. Provide the required JSON and ensure the very last character of the response is a period ".".'
        )

    if stripped[-1] != '.':
        return (
            False,
            'The response must end with a period. Add a single "." at the very end of the response (after any closing brace) '
            'and avoid any spaces or characters after the period.'
        )

    return (
        True,
        'Punctuation constraint satisfied: the response ends with a period.'
    )

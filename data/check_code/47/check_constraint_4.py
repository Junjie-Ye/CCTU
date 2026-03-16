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
 Your response must be between 10 and 30 words in length to ensure conciseness while including the exact casualty count. Additionally, the agent must use an appropriate number of tool calls to arrive at the answer, the total number of interaction turns must not exceed a reasonable limit, and the final answer must be formatted as a valid JSON object with a key 'casualties' containing the exact number of fatalities.

response_constraints_non_length:
- idx 4: ('Response', 'Format', "The answer must be formatted as a valid JSON object with a key 'casualties' containing the exact number of fatalities.")
"""

import json
from json.decoder import JSONDecodeError, JSONDecoder
from typing import Tuple, Any

# Helper: attempt to parse a standalone JSON object from the entire response


def _parse_standalone_json_object(text: str) -> Tuple[bool, str, Any]:
    """
    Parses a standalone JSON object from 'text'.
    Returns (ok, error_message, obj). If ok is True, obj is the parsed dict.
    Fails if:
      - wrapped in code fences or contains markdown
      - not valid JSON
      - not an object
      - extra non-whitespace characters exist outside the JSON object
    """
    if text is None:
        return False, "Response is empty. Provide a single JSON object like: {\"casualties\": 123}", None

    s = text.strip()

    # Reject Markdown code fences or any backticks
    if "```" in s or s.startswith("`") or s.endswith("`"):
        return False, "Do not use code fences or backticks. Output only the raw JSON object.", None

    # Use raw_decode to ensure no trailing non-whitespace content exists
    decoder = JSONDecoder()
    try:
        obj, end = decoder.raw_decode(s)
    except JSONDecodeError as e:
        return False, f"Invalid JSON: {e}. Output must be a single JSON object like: {{\"casualties\": 123}}", None

    # Ensure only whitespace after the JSON object
    tail = s[end:].strip()
    if tail:
        return False, "Output must contain only a single JSON object with no extra text before or after it.", None

    if not isinstance(obj, dict):
        return False, "Top-level value must be a JSON object. Example: {\"casualties\": 123}", None

    return True, "", obj


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates the 'format' response constraint:
    - The response must be a standalone, valid JSON object.
    - It must contain a key 'casualties'.
    - 'casualties' must be a non-negative integer (no quotes, no decimals, not boolean).
    Returns (is_valid, message). Message is in English and provides corrective guidance.
    """
    ok, err, obj = _parse_standalone_json_object(response)
    if not ok:
        return False, err

    if "casualties" not in obj:
        return False, "Missing key 'casualties'. Provide: {\"casualties\": <non-negative integer>}"

    value = obj["casualties"]

    # Reject null
    if value is None:
        return False, "The value of 'casualties' cannot be null. Use a non-negative integer, e.g., {\"casualties\": 0}"

    # Reject booleans (bool is subclass of int in Python)
    if isinstance(value, bool):
        return False, "The value of 'casualties' must be an integer, not boolean. Example: {\"casualties\": 123}"

    # Accept only plain integers
    if isinstance(value, int):
        if value < 0:
            return False, "The value of 'casualties' must be a non-negative integer. Example: {\"casualties\": 0}"
        # Valid
        return True, "Valid format. Keep only a single JSON object with a non-negative integer 'casualties' value."

    # Provide actionable guidance for common incorrect types
    if isinstance(value, float):
        return False, "The value of 'casualties' must be an integer without decimals. Example: {\"casualties\": 123}"

    if isinstance(value, str):
        return False, "The value of 'casualties' must be a number, not a quoted string. Example: {\"casualties\": 123}"

    # Any other type (arrays, objects, etc.)
    return False, "The value of 'casualties' must be a single non-negative integer. Example: {\"casualties\": 123}"

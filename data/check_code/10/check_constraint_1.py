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
 You must answer by calling the provided tools. The total number of tool calls across all interaction turns must not exceed 3. The final answer must be formatted as a valid JSON object with a key "location" specifying the country where the event occurred.

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'JSON (The answer must be structured as a valid JSON object with a key "location" containing the country name.)')
"""

import json
from typing import Tuple, Any


def _parse_json_object(response: str) -> Tuple[bool, Any, str]:
    """
    Helper to strictly parse a JSON object from the response.
    Returns (ok, obj, message). On success, obj is the parsed dict.
    """
    if response is None:
        return False, None, "Response is None. Return only a JSON object like: {\"location\": \"Country\"}."
    text = response.strip()
    if not text:
        return False, None, "Response is empty. Return only a JSON object like: {\"location\": \"Country\"}."
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return (
            False,
            None,
            "Invalid JSON. Use double quotes and no extra text or code fences. "
            f"Example: {{\"location\": \"United Kingdom\"}}. JSON error: {e}"
        )
    if not isinstance(data, dict):
        return (
            False,
            None,
            "Top-level JSON must be an object (dictionary). Return exactly: {\"location\": \"Country\"} with no extra keys."
        )
    return True, data, "OK"


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is:
    - A valid JSON object.
    - Contains exactly one key: 'location' (lowercase).
    - The value is a non-empty string (the country name).
    - No extra text outside the JSON.
    """
    ok, obj, msg = _parse_json_object(response)
    if not ok:
        return False, msg

    keys = list(obj.keys())
    if len(keys) != 1:
        extra = [k for k in keys if k != "location"]
        missing = "location" not in obj
        if missing and extra:
            return False, (
                "The JSON must contain exactly one key named \"location\" and nothing else. "
                "Remove extra keys and add the required key. Example: {\"location\": \"United Kingdom\"}."
            )
        if missing:
            return False, (
                "Missing required key \"location\". Return exactly one key: "
                "{\"location\": \"Country\"}."
            )
        # Has 'location' plus extras
        return False, (
            "Only one key is allowed: \"location\". Remove all other keys. "
            "Example: {\"location\": \"United Kingdom\"}."
        )

    if "location" not in obj:
        return False, (
            "The only allowed key is exactly \"location\" (lowercase). "
            "Use: {\"location\": \"Country\"}."
        )

    val = obj["location"]
    if not isinstance(val, str):
        return False, (
            "The value of \"location\" must be a string containing the country name. "
            "Example: {\"location\": \"United Kingdom\"}."
        )

    if not val.strip():
        return False, (
            "The \"location\" value must be a non-empty country name string. "
            "Example: {\"location\": \"United Kingdom\"}."
        )

    # Passed all checks
    return True, (
        "Valid format. Keep exactly this structure: a single JSON object with one key "
        "\"location\" mapped to a non-empty country name string, and no additional text."
    )

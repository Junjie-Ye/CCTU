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
 The solution must involve a total number of tool calls between 1 and 2, inclusive. The response must be structured as a valid JSON object with a "date" key containing the answer in [YYYY-MM-DD] format. Additionally, the tool military_event_search can be used at most once during the solution process.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Response, Delimiting identifier, Must include the date in the format [YYYY-MM-DD] to clearly indicate the answer)')
- idx 3: ('Response', 'Format', 'JSON (Mandates that the agent\'s entire response must be structured as a valid JSON object with a "date" key containing the answer.)')
"""

import json
import re
from typing import Tuple, Optional
from datetime import datetime

# Helper: attempt to parse the entire response as JSON and ensure no extra content exists.


def _parse_json_strict(response: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Parse the response as JSON. Returns (obj, error_message).
    Ensures the top-level is a dict and that the input is exactly JSON (no extra non-JSON text).
    """
    text = (response or "").strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        return None, (
            f"JSON parsing failed: {str(e)}. The response must be exactly a JSON object and nothing else."
        )
    if not isinstance(obj, dict):
        return None, "Top-level JSON must be an object (dictionary), not an array, string, or number."
    return obj, None

# Helper: validate bare date format YYYY-MM-DD with calendar correctness.


def _is_valid_iso_date(date_str: str) -> bool:
    """
    Validate a date string strictly matching YYYY-MM-DD and representing a real calendar date.
    """
    if not isinstance(date_str, str):
        return False
    s = date_str.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the 'format' constraint:
    - The entire response must be exactly a valid JSON object.
    - It must contain a single top-level key: "date".
    - The value of "date" must be a string.
    """
    obj, err = _parse_json_strict(response)
    if err:
        return False, (
            "Invalid format. Your response must be exactly one JSON object with no extra text, "
            'markdown, or explanations. Use a single top-level key "date". '
            'Example: {"date": "2023-04-15"}'
        )

    keys = list(obj.keys())
    if len(keys) != 1 or "date" not in obj:
        return False, (
            'Invalid JSON structure. Provide exactly one key named "date" and no other keys. '
            'Example: {"date": "2023-04-15"}'
        )

    if not isinstance(obj["date"], str):
        return False, (
            'The value of "date" must be a JSON string. Wrap the date in quotes. '
            'Example: {"date": "2023-04-15"}'
        )

    return True, 'Valid JSON format with a single "date" string.'


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the 'identifiers' constraint (UPDATED):
    - The JSON "date" value must be exactly an ISO date like "YYYY-MM-DD".
    - No bracketed form is allowed/required.
    """
    obj, err = _parse_json_strict(response)
    if err:
        return False, (
            'Response is not valid JSON. Output exactly one JSON object with a single key "date". '
            'Then ensure the date is in "YYYY-MM-DD". Example: {"date": "2023-04-15"}'
        )

    if "date" not in obj or not isinstance(obj["date"], str):
        return False, (
            'Missing or invalid "date" string. Provide a "date" key whose value is a string in the '
            'format "YYYY-MM-DD". Example: {"date": "2023-04-15"}'
        )

    value = obj["date"].strip()
    if not _is_valid_iso_date(value):
        return False, (
            'Invalid date identifier. The "date" value must be exactly "YYYY-MM-DD" with a real '
            "calendar date, zero-padded month/day, and no extra characters. "
            'Examples: "2023-04-15", "2024-02-29".'
        )

    return True, 'Valid ISO date identifier "YYYY-MM-DD" detected in the "date" value.'

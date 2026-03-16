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
 Your answer must be concise and not exceed 150 characters. Additionally, your final response must contain a valid JSON object, including key-value pairs and adhering to proper syntax rules to ensure it can be successfully parsed without errors. You are allowed a maximum of 3 interaction turns to retrieve the required information. The final response must end with a period to ensure proper sentence closure. If the tools successfully retrieve the target result, the final answer must identify this result by prefixing it with the label 'Life Expectancy: '

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'The answer must contain a valid JSON object, including key-value pairs and adhering to proper syntax rules to ensure it can be successfully parsed without errors.')
- idx 2: ('Response', 'Identifiers', "If the tools successfully retrieve the target result, the final answer must identify this result by prefixing it with the label 'Life Expectancy: '")
- idx 4: ('Response', 'Punctuation', 'The final value in json must end with a period to ensure proper sentence closure.')
"""

import json
from typing import Tuple, Any, Optional


# ---------------------------
# Helper functions (shared)
# ---------------------------

def _parse_json_object(response: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Try to parse the response as a standalone JSON object.
    Returns (obj, None) on success, or (None, error_message) on failure.
    """
    if response is None:
        return None, "Response is None; provide a JSON object string."
    text = response.strip()
    if not text:
        return None, "Response is empty; provide a JSON object like {\"key\": \"value\"}."
    try:
        parsed = json.loads(text)
    except Exception as e:
        return None, f"Invalid JSON syntax: {e}. Output only a JSON object, no extra text."
    if not isinstance(parsed, dict):
        return None, "Top-level JSON must be an object (e.g., {\"key\": \"value\"}), not an array, string, number, or null."
    return parsed, None


def _get_single_pair(obj: dict) -> Tuple[Optional[Tuple[str, Any]], Optional[str]]:
    """
    Ensure the JSON object has exactly one key-value pair and return it.
    """
    if len(obj) != 1:
        return None, "Use exactly one key-value pair in the JSON object."
    key = next(iter(obj.keys()))
    value = obj[key]
    return (key, value), None


# ---------------------------
# Validators (per constraint)
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Constraint: The answer must contain a valid JSON object, including key-value pairs and adhering to proper syntax
    so it can be parsed without errors.

    This validator enforces:
    - Response is a standalone, syntactically valid JSON.
    - The top-level value is an object.
    - The object contains exactly one key-value pair.
    - The single value is a string (so it can carry the required label and punctuation).
    """
    obj, err = _parse_json_object(response)
    if err:
        return False, err

    pair, pair_err = _get_single_pair(obj)
    if pair_err:
        return False, pair_err

    key, value = pair
    if not isinstance(key, str) or key == "":
        return False, "The JSON key must be a non-empty string."
    if not isinstance(value, str):
        return False, "The JSON value must be a single string, not a number, object, or array."

    return True, "Valid format: standalone JSON object with exactly one key and a string value."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Constraint: If the tools successfully retrieve the target result, the final answer must identify this result by
    prefixing it with the label 'Life Expectancy: '.

    This validator checks that the single JSON value starts with the exact prefix 'Life Expectancy: '.
    """
    obj, err = _parse_json_object(response)
    if err:
        return False, f"{err} Fix the format first, then ensure the value starts with 'Life Expectancy: '."

    pair, pair_err = _get_single_pair(obj)
    if pair_err:
        return False, f"{pair_err} Then start the value with the exact prefix 'Life Expectancy: '."

    _, value = pair
    if not isinstance(value, str):
        return False, "The JSON value must be a string that begins with 'Life Expectancy: '."
    expected_prefix = "Life Expectancy: "
    if not value.startswith(expected_prefix):
        return False, (
            "Prefix the value with the exact label 'Life Expectancy: ' (including the trailing space). "
            "Example: {\"result\": \"Life Expectancy: 68.3 years.\"}"
        )

    return True, "Valid identifiers: the value starts with 'Life Expectancy: '."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Constraint: The final value in JSON must end with a period to ensure proper sentence closure.
    """
    obj, err = _parse_json_object(response)
    if err:
        return False, f"{err} Fix the format first, then ensure the value ends with a period."

    pair, pair_err = _get_single_pair(obj)
    if pair_err:
        return False, f"{pair_err} Then ensure the single value ends with a period."

    _, value = pair
    if not isinstance(value, str):
        return False, "The JSON value must be a string that ends with a period."
    trimmed = value.rstrip()
    if not trimmed.endswith("."):
        return False, (
            "End the value with a period '.' as the final character (no extra text after it). "
            "Example: {\"result\": \"Life Expectancy: 68.3 years.\"}"
        )

    return True, "Valid punctuation: the value ends with a period."

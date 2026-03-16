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
 The AI Agent must complete at least 2 interaction turns before providing a final answer. The final answer must be at most 10 words in length to ensure conciseness. Additionally, the final answer must be structured as a valid JSON object with the company name as the only key-value pair.

response_constraints_non_length:
- idx 2: ('Response', 'Format', 'Must be structured as a valid JSON object with the company name as the only key-value pair.')
"""

import json
from typing import Tuple


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that `response` is:
      - A valid JSON string
      - Representing a JSON object (dict)
      - Containing exactly one key-value pair
      - Whose value is a non-empty string (the company name)

    Returns:
      (True, detail) if valid
      (False, actionable_error_message) if invalid
    """
    # 1) Must be valid JSON with no extra text
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as e:
        return (
            False,
            "Response must be a valid JSON object with exactly one key-value pair. "
            "Ensure proper JSON syntax: use double quotes for keys and string values, "
            "no trailing commas, and no extra text outside the JSON. "
            f"JSON parsing error: {e}. Example of a valid response: "
            '{"company": "Acme Inc."}'
        )

    # 2) Must be a JSON object (not array, string, number, etc.)
    if not isinstance(parsed, dict):
        return (
            False,
            "Response must be a JSON object (e.g., {\"company\": \"Acme Inc.\"}), "
            "not an array, string, number, or boolean."
        )

    # 3) Must have exactly one key-value pair
    if len(parsed) == 0:
        return (
            False,
            "JSON object must contain exactly one key-value pair. "
            "Currently it has none. Provide only the company name as the sole pair. "
            "Example: {\"company\": \"Acme Inc.\"}"
        )
    if len(parsed) > 1:
        return (
            False,
            "JSON object must contain exactly one key-value pair. "
            "Currently it has multiple keys. Keep only one pair with the company name. "
            "Example: {\"company\": \"Acme Inc.\"}"
        )

    # 4) The single value must be a non-empty string (the company name)
    key, value = next(iter(parsed.items()))
    if not isinstance(value, str):
        return (
            False,
            "The value of the single key must be a string containing the company name. "
            f"Found type '{type(value).__name__}'. Example: {{\"{key}\": \"Acme Inc.\"}}"
        )
    if value.strip() == "":
        return (
            False,
            "The company name string must be non-empty. "
            f"Example: {{\"{key}\": \"Acme Inc.\"}}"
        )

    return (
        True,
        "Valid format: JSON object with exactly one key and a non-empty string value (company name)."
    )

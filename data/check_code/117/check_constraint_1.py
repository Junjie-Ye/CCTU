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
 To answer this, if the agent intends to retrieve speaker data for all three languages, it must invoke both the `language_speaker_estimator` and `global_language_statistics_v2` tools in a single coordinated step. The agent may invoke the 'language_speaker_estimator' tool at most 2 times and the 'global_language_statistics_v2' tool at most 1 time. Your final answer must be a valid JSON object containing the three languages and their speaker counts as key-value pairs, with numerical values formatted as strings to accommodate potential tool output variations.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "The agent's final answer must be a valid JSON object containing the three languages and their speaker counts as key-value pairs, with numerical values formatted as strings to accommodate potential tool output variations.")
"""

import json
import re
from typing import Tuple, Dict, Any

# Helper: check if a string looks like a numeric value (very permissive).
# We only require at least one digit to accommodate variations (e.g., "1,120,000,000", "1.1e9", "1.2 billion").
_digit_regex = re.compile(r"\d")


def _format_example() -> str:
    return '{"Mandarin": "1110000000", "Spanish": "493000000", "English": "1350000000"}'


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
      - The entire response is exactly a valid JSON object (no markdown fences, no labels, no extra text).
      - The object contains exactly the keys: Mandarin, Spanish, English.
      - Each corresponding value is a string that contains at least one digit (numeric value formatted as a string).
    Returns:
      (is_valid, message)
    """
    if response is None:
        return (
            False,
            "Response is None. Return only a JSON object with exactly the three keys: Mandarin, Spanish, English. "
            f"Example: {_format_example()}",
        )

    raw = response.strip()
    if not raw:
        return (
            False,
            "Response is empty. Return only a JSON object with exactly the three keys: Mandarin, Spanish, English. "
            f"Example: {_format_example()}",
        )

    # Disallow common wrappers (markdown code fences or labeled sections).
    if raw.startswith("```") or raw.endswith("```") or "[FINAL ANSWER]" in raw or "[FINAL" in raw:
        return (
            False,
            "Do not include markdown code fences or section labels. Return ONLY the raw JSON object. "
            f"Example: {_format_example()}",
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return (
            False,
            f"Response is not valid JSON ({e}). Return ONLY a valid JSON object with no extra text. "
            f"Example: {_format_example()}",
        )

    if not isinstance(data, dict):
        return (
            False,
            "Top-level JSON must be an object (dictionary), not an array or other type. "
            f"Return exactly: {_format_example()}",
        )

    required_keys = {"Mandarin", "Spanish", "English"}
    present_keys = set(data.keys())

    missing = required_keys - present_keys
    extra = present_keys - required_keys

    if missing or extra:
        details = []
        if missing:
            details.append(f"missing keys: {sorted(missing)}")
        if extra:
            details.append(
                f"unexpected keys: {sorted(extra)} (only the three required keys are allowed)")
        return (
            False,
            "JSON object must contain exactly three keys: Mandarin, Spanish, English. "
            + "; ".join(details)
            + ". "
            f"Return exactly: {_format_example()}",
        )

    # Validate values: must be strings with at least one digit (to indicate a numeric value encoded as string).
    value_issues = []
    for lang in ["Mandarin", "Spanish", "English"]:
        val = data.get(lang)
        if not isinstance(val, str):
            value_issues.append(
                f"{lang}: value must be a string (found {type(val).__name__})")
            continue
        if not val.strip():
            value_issues.append(f"{lang}: string cannot be empty")
            continue
        if not _digit_regex.search(val):
            value_issues.append(
                f"{lang}: string must contain at least one digit (e.g., '1110000000' or '1.11e9')")

    if value_issues:
        return (
            False,
            "All values must be numeric values formatted as strings and contain at least one digit. "
            + "; ".join(value_issues)
            + ". "
            f"Example: {_format_example()}",
        )

    return True, "Valid: response is a JSON object with exactly the required keys and string-formatted numeric values."

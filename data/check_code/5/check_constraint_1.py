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
 Your response must be a valid JSON object containing only a key 'president' with the winning candidate's name as the value. The 'president' value must not include any punctuation marks at the end. The JSON response must contain between 30 and 50 characters to ensure sufficient detail while maintaining conciseness. You are allowed at most 3 interaction rounds to solve this task, after which you must provide the final answer. Additionally, the event_outcome_retriever tool may only be used once during the solution process. The total number of tool calls across all interaction turns must be between 1 and 3 (inclusive).

response_constraints_non_length:
- idx 0: ('Response', 'Format', "The response must be a valid JSON object containing a key 'president' with the winning candidate's name as the value. All other keys are disallowed.")
- idx 1: ('Response', 'Punctuation', "The 'president' value in the JSON response must not end with any punctuation mark, including periods, commas, or apostrophes.")
"""

import json
import string
from typing import Tuple, Optional, Dict, Any

# Helper: robust set of punctuation characters (ASCII + common Unicode)
ASCII_PUNCT = set(string.punctuation)
UNICODE_PUNCT = set(
    ",。!?、;:‘’“”·—...()《》【】「」『』?!;.,、.‧‐–—‚„‹›«»¡¿‐‐‐—―·。・❜❛❝❞")
PUNCTUATION_CHARS = ASCII_PUNCT | UNICODE_PUNCT


def _parse_json_object(response: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Try to parse the response as a JSON object (dict).
    Returns (dict, None) on success, or (None, error_message) on failure.
    """
    if response is None:
        return None, "Response is None; it must be a JSON object string like {'president': 'Name'}."
    text = response.strip()
    try:
        data = json.loads(text)
    except Exception as e:
        return None, (
            "Response is not valid JSON. Provide only a JSON object with double-quoted keys/values, "
            "e.g., {\"president\":\"First Last\"}. Remove any extra commentary or wrappers."
        )
    if not isinstance(data, dict):
        return None, "Top-level JSON must be an object. Use {\"president\":\"First Last\"}, not an array or primitive."
    return data, None


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response is valid JSON.
    - The top-level value is an object.
    - It contains exactly one key: 'president'.
    - The 'president' value is a non-empty string (after trimming).
    - No other keys are present.
    """
    data, parse_err = _parse_json_object(response)
    if parse_err:
        return False, parse_err

    errors = []

    # 1) Keys must be exactly {'president'}
    keys = set(data.keys())
    if "president" not in data:
        errors.append(
            "Missing required key 'president'. Include it at the top level.")
    if len(keys) != 1 or keys != {"president"}:
        extra = [k for k in keys if k != "president"]
        if extra:
            errors.append(
                f"Disallowed keys present: {extra}. Only 'president' is permitted at the top level.")
        if "president" not in keys:
            errors.append(
                "The only allowed key is 'president' with the winner's name as the value.")

    # 2) Value must be a non-empty string
    if "president" in data:
        if not isinstance(data["president"], str):
            errors.append(
                "The value of 'president' must be a string containing the winner's name.")
        else:
            if data["president"].strip() == "":
                errors.append(
                    "The 'president' value must be a non-empty string (not just whitespace).")

    if errors:
        return False, (
            "Format violation: " + " ".join(errors) +
            " Provide exactly: {\"president\":\"First Middle Last\"} with no additional keys or text."
        )

    return True, (
        "Format is valid: JSON object with a single 'president' key whose value is a non-empty string."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the 'president' string does not end with any punctuation mark.
    Internal punctuation is allowed; only the final character (ignoring trailing whitespace) must not be punctuation.
    """
    data, parse_err = _parse_json_object(response)
    if parse_err:
        return False, (
            "Punctuation check requires valid JSON first. " +
            parse_err
        )

    if "president" not in data:
        return False, "Missing key 'president'. Include it and ensure its value does not end with punctuation."

    name = data["president"]
    if not isinstance(name, str):
        return False, "The 'president' value must be a string. Provide a textual name without trailing punctuation."

    trimmed = name.rstrip()
    if trimmed == "":
        return False, "The 'president' value is empty after trimming. Provide a non-empty name without trailing punctuation."

    last_char = trimmed[-1]
    if last_char in PUNCTUATION_CHARS:
        return False, (
            "The 'president' value ends with a punctuation mark "
            f"('{last_char}'). Remove any trailing punctuation such as periods, commas, or apostrophes. "
            "Example: {\"president\":\"First Middle Last\"}"
        )

    return True, "Punctuation is valid: the 'president' value does not end with a punctuation mark."

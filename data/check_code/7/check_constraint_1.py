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
 The answer must be between 15 and 20 words (inclusive), end with a period, and use a comma to separate the two country names. Additionally, the response must include a valid JSON object containing "countries" (array of two country names) and "date" (string in "March 2023" format) fields. The solution must use between 1 and 5 tool calls across all interaction turns, and the total number of interaction rounds must fall within the range of 2 to 5.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'Ending punctuation (.)')
- idx 3: ('Response', 'Identifiers', '(Response, Delimiting identifier, Must include a comma (,) to separate the two country names in the response.)')
- idx 4: ('Response', 'Format', '(Response, JSON, Must include valid JSON object containing "countries" (array of two country names) and "date" (string in "March 2023" format) fields with proper syntax.)')
"""

import json
import re
from typing import Tuple, Optional


# ---------------------------
# Helpers shared by validators
# ---------------------------

MONTHS_RE = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_RE = re.compile(rf"^{MONTHS_RE}\s+\d{{4}}$")


def _find_first_json_object_span(text: str) -> Optional[Tuple[int, int]]:
    """
    Return (start, end) indices of the first balanced JSON object in text,
    accounting for quoted strings and escaped characters. Returns None if not found.
    """
    in_string = False
    escape = False
    depth = 0
    start = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
            # Inside string: braces do not count
            continue

        # Not in string
        if ch == '"':
            in_string = True
            continue

        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    return (start, i + 1)
    return None


def _extract_json_object(text: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Attempt to extract and parse the first JSON object from the given text.
    Returns (obj, err). If obj is None, err contains a detailed reason.
    """
    span = _find_first_json_object_span(text)
    if span is None:
        return None, "No JSON object found. Include one {...} with valid JSON syntax (double quotes, commas)."
    start, end = span
    json_str = text[start:end]
    try:
        obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        return None, (
            f"Invalid JSON syntax: {e}. Ensure double quotes for keys/strings, commas between items, "
            f"and no trailing commas."
        )
    if not isinstance(obj, dict):
        return None, "Top-level JSON must be an object (i.e., {...}), not an array or other type."
    return obj, None


def _validate_countries_field(obj: dict) -> Tuple[bool, str]:
    """
    Validate 'countries' field exists, is a list of exactly two non-empty strings.
    """
    if "countries" not in obj:
        return False, 'Missing "countries" field. Add: "countries": ["Country A", "Country B"].'
    countries = obj["countries"]
    if not isinstance(countries, list):
        return False, '"countries" must be an array of two strings, e.g., ["Country A", "Country B"].'
    if len(countries) != 2:
        return False, '"countries" must contain exactly two items, e.g., ["Country A", "Country B"].'
    if not all(isinstance(c, str) and c.strip() for c in countries):
        return False, 'Each item in "countries" must be a non-empty string, e.g., "Country A".'
    return True, "OK"


def _validate_date_field(obj: dict) -> Tuple[bool, str]:
    """
    Validate 'date' field exists, is a string in 'Month YYYY' format (e.g., 'March 2023').
    """
    if "date" not in obj:
        return False, 'Missing "date" field. Add: "date": "March 2023" (Month and four-digit year).'
    date_val = obj["date"]
    if not isinstance(date_val, str):
        return False, '"date" must be a string in the format "Month YYYY", e.g., "March 2023".'
    if not DATE_RE.match(date_val.strip()):
        return False, (
            '"date" must match "Month YYYY" (e.g., "March 2023"). Use full month name and a four-digit year.'
        )
    return True, "OK"


# ---------------------------
# Constraint validators
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Response, JSON format constraint:
    Must include a valid JSON object containing "countries" (array of two country names)
    and "date" (string in "March 2023" format) fields with proper syntax.
    """
    if not isinstance(response, str) or not response.strip():
        return False, "Response is empty. Include text with a valid JSON object."

    obj, err = _extract_json_object(response)
    if err:
        return False, err

    ok_c, msg_c = _validate_countries_field(obj)
    if not ok_c:
        return False, msg_c

    ok_d, msg_d = _validate_date_field(obj)
    if not ok_d:
        return False, msg_d

    return True, 'Valid format: JSON object with "countries" (two strings) and "date" ("Month YYYY").'


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Response, punctuation constraint:
    The entire response must end with a period (.).
    """
    if not isinstance(response, str) or not response.strip():
        return False, "Response is empty. End the full response with a period (.)"
    trimmed = response.rstrip()
    if not trimmed.endswith("."):
        return False, (
            "The final non-whitespace character must be a period. Append a single '.' at the very end of the response "
            "(e.g., after the closing brace of the JSON object)."
        )
    return True, "Valid punctuation: response ends with a period."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Response, identifiers (delimiting) constraint:
    Must include a comma (,) to separate the two country names in the response.
    This is satisfied if:
      - The JSON array 'countries' contains exactly two items (JSON inherently uses a comma between them), OR
      - The plain text contains two name-like phrases separated by a single comma.
    """
    if not isinstance(response, str) or not response.strip():
        return False, "Response is empty. Include two country names separated by a comma."

    # Path A: If a valid JSON countries array of length 2 exists, the comma requirement is inherently met.
    obj, err = _extract_json_object(response)
    if err is None:
        ok_c, _ = _validate_countries_field(obj)
        if ok_c and len(obj["countries"]) == 2:
            return True, "Valid identifiers: two country names are comma-separated within the JSON array."

    # Path B: Fallback to textual pattern: two name-like phrases separated by a comma.
    # This pattern matches two sequences of letters/spaces/hyphens with a comma between.
    comma_pair_re = re.compile(
        r"\b[A-Za-z][A-Za-z\-\s]*[A-Za-z]\s*,\s*[A-Za-z][A-Za-z\-\s]*[A-Za-z]\b"
    )
    if comma_pair_re.search(response):
        return True, "Valid identifiers: found two name-like phrases separated by a comma."

    return False, (
        "Missing comma-separated country pair. Include exactly two country names separated by one comma, "
        'e.g., Country A, Country B. If using JSON, ensure "countries": ["Country A", "Country B"].'
    )

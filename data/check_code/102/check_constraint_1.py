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
 The final answer must be between 50 and 150 characters in length to ensure clarity and conciseness, must explicitly state the casualty numbers for each event separated by a semicolon followed by the total in the format "Prüm: X; Kemi: Y; Total: Z", and the agent may call the 'historical_event_info_retriever' tool at most 2 times during the task.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', "Must include the casualty numbers for each event separated by a semicolon followed by the total in the format 'Prüm: X; Kemi: Y; Total: Z'")
"""

import re
from typing import Tuple

# Pre-compiled regex to detect the exact required identifier phrases and structure.
# Accepts integers with optional thousands separators (e.g., 1,234).
# The pattern is searched within the response (does not require the entire response to be exactly this).
IDENTIFIER_PATTERN = re.compile(
    r"Prüm:\s*(?P<prum>\d{1,3}(?:,\d{3})*|\d+)\s*;\s*Kemi:\s*(?P<kemi>\d{1,3}(?:,\d{3})*|\d+)\s*;\s*Total:\s*(?P<total>\d{1,3}(?:,\d{3})*|\d+)",
    re.UNICODE
)


def _contains_all_identifiers(response: str) -> Tuple[bool, str]:
    """
    Helper to check presence of required literal identifiers and separators,
    independent of numeric correctness.
    """
    missing = []
    if "Prüm:" not in response:
        missing.append("literal 'Prüm:' (with ü)")
    if "Kemi:" not in response:
        missing.append("literal 'Kemi:'")
    if "Total:" not in response:
        missing.append("literal 'Total:'")
    if ";" not in response:
        missing.append("ASCII semicolons ';' as separators")
    if missing:
        return False, "Missing or misspelled components: " + ", ".join(missing)
    return True, "All key literals and separators found."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'identifiers' constraint:
    - The answer must include the exact phrase structure:
      'Prüm: X; Kemi: Y; Total: Z'
    - Prüm, Kemi, and Total labels must appear exactly as spelled (including ü in Prüm).
    - X, Y, Z must be numeric (digits, optionally with thousands separators like 1,234).
    - ASCII semicolons must separate the segments in the given order.

    Returns:
        (bool, str): True with guidance if valid; False with detailed correction steps otherwise.
    """
    if not isinstance(response, str) or not response.strip():
        return False, (
            "Response is empty or not a string. Provide a non-empty string like: "
            "Prüm: 62; Kemi: 14; Total: 76"
        )

    # First, check required identifiers and separators are present in some form.
    has_all_idents, ident_msg = _contains_all_identifiers(response)
    if not has_all_idents:
        return False, (
            f"{ident_msg}. Use the exact structure and order with ASCII semicolons. "
            "Example: Prüm: 62; Kemi: 14; Total: 76"
        )

    # Now enforce the required ordering and numeric formats via regex search.
    m = IDENTIFIER_PATTERN.search(response)
    if not m:
        return False, (
            "The required segment was not found in the correct order/format. "
            "Ensure the exact sequence with spaces and ASCII semicolons: "
            "'Prüm: X; Kemi: Y; Total: Z' where X, Y, Z are integers "
            "(optionally with thousands separators, e.g., 1,234). "
            "Example: Prüm: 62; Kemi: 14; Total: 76"
        )

    # Optional extra validation: ensure captured numbers are syntactically valid integers
    # (already guaranteed by regex), but provide clearer guidance if a non-digit slipped in.
    for label in ("prum", "kemi", "total"):
        val = m.group(label)
        # Remove commas and validate it's digits only
        if not val.replace(",", "").isdigit():
            return False, (
                f"The value for {label} must be a number (digits only, commas allowed for thousands). "
                f"Found: '{val}'. Example: Prüm: 1,200; Kemi: 350; Total: 1,550"
            )

    return True, (
        "Identifiers constraint satisfied: found 'Prüm: X; Kemi: Y; Total: Z' with numeric values. "
        "Keep labels and ASCII semicolons exactly as shown."
    )

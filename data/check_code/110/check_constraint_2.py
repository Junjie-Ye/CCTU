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
 You must obtain all information through tool calls, ensure that no more than 3 rounds of interaction are used, limit each unique tool to a maximum of one invocation in the process, and include the phrase '---' in your response to clearly separate the dates of the two events.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', "(Response, Delimiting identifier, The agent's response must include the phrase '---' between the dates of the two events to clearly separate them in the final answer.)")
"""

import re
from typing import List, Tuple, Pattern, Match, Optional

# Precompile a robust date-detection regex that covers common human-readable formats:
# - ISO: 2024-01-31
# - US/Intl numeric: 01/31/2024 or 31/01/2024 (2 or 4 digit year)
# - Textual: January 31, 2024 | Jan 31, 2024 | 31 January 2024 | 31 Jan 2024
_MONTHS = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)

DATE_REGEX: Pattern = re.compile(
    rf"""
    (
        \b\d{{4}}-\d{{2}}-\d{{2}}\b                                  # ISO YYYY-MM-DD
      | \b\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}\b                      # 1-2 digit MM/DD/YYYY or DD/MM/YYYY
      | \b(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,\s*\d{{4}})?\b # Month DD(, YYYY)
      | \b\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b                      # DD Month YYYY
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

DELIM: str = "---"


def _find_all_indices(haystack: str, needle: str) -> List[int]:
    """Return all start indices where 'needle' occurs in 'haystack' (non-overlapping)."""
    indices = []
    start = 0
    while True:
        i = haystack.find(needle, start)
        if i == -1:
            break
        indices.append(i)
        start = i + len(needle)
    return indices


def _has_date(text: str) -> bool:
    """Check if at least one date-like token exists in the text."""
    return DATE_REGEX.search(text) is not None


def _dates_near_delimiter(response: str, delim_index: int, window: int = 150) -> Tuple[bool, bool]:
    """
    Determine if there is a date on the left and right within a given window
    around the delimiter position.
    """
    left_context_start = max(0, delim_index - window)
    left_context = response[left_context_start:delim_index]
    right_context_end = min(len(response), delim_index + len(DELIM) + window)
    right_context = response[delim_index + len(DELIM):right_context_end]

    left_has_date = _has_date(left_context)
    right_has_date = _has_date(right_context)
    return left_has_date, right_has_date


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'identifiers' response constraint:
    - The final answer must include the exact delimiter '---' placed between
      the dates of the two events to clearly separate them.

    Returns:
        (is_valid, message)
        is_valid: True if the constraint is satisfied.
        message: Detailed English guidance on what is correct or how to fix.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The final answer must be a non-empty string. Include two explicit dates and place the exact delimiter '---' between them, e.g., 2023-05-10 --- 2024-01-02."
        )

    indices = _find_all_indices(response, DELIM)
    if not indices:
        return (
            False,
            "Missing required delimiter. Insert the exact string '---' between the two event dates in your final answer. Example formats that pass: "
            "'2023-05-10 --- 2024-01-02', 'January 5, 2023 --- Feb 14, 2024', or '05/01/2023 --- 14/02/2024'. "
            "Do not use em dashes or other characters; use exactly three hyphens."
        )

    # Check if at least one occurrence of '---' separates two detectable dates.
    for idx in indices:
        left_has_date, right_has_date = _dates_near_delimiter(
            response, idx, window=150)
        if left_has_date and right_has_date:
            return (
                True,
                "PASS: Found the required '---' delimiter used between two detected date strings in the final answer."
            )

    # If we reached here, '---' exists but not between two recognizable dates
    return (
        False,
        "The delimiter '---' is present but not positioned between two explicit date strings. "
        "Revise your final answer so that one valid date appears immediately before the delimiter and another valid date appears after it. "
        "Acceptable date formats include: YYYY-MM-DD (e.g., 2024-01-31), Month DD, YYYY (e.g., January 31, 2024), "
        "DD Month YYYY (e.g., 31 January 2024), or MM/DD/YYYY / DD/MM/YYYY. "
        "Example correction:\n"
        "2023-05-10 --- 2024-01-02"
    )

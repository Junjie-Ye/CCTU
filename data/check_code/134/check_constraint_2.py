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
 You must ensure that during the problem-solving process: 1) The number of unique tool types invoked simultaneously in any single interaction turn is between 1 and 2 (inclusive); 2) At least one interaction turn must include exactly 1 unique tool type; 3) No turn may exceed 2 unique tool types; 4) The total number of interaction turns must not exceed 3; 5) The final response must conclude with the phrase "Days: [number]" where [number] is the calculated difference in days; 6) The response must not include any punctuation marks in the ending phrase; and 7) The agent may invoke the `historical_event_finder` tool at most 2 times during the entire problem-solving process.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', 'The response must conclude with the phrase "Days: [number]" where [number] is the calculated difference in days.')
- idx 2: ('Response', 'Punctuation', 'The response must not include any punctuation marks in the ending phrase')
"""

import re
import unicodedata
from typing import Tuple, List

# Helper: extract the final (ending) line, trimmed of trailing whitespace.


def _get_ending_line(response: str) -> str:
    if response is None:
        return ""
    stripped = response.rstrip("\n\r\t ")
    if not stripped:
        return ""
    lines = stripped.splitlines()
    return lines[-1].strip()


ALLOWED_ENDING_PUNCT = {":", "："}
# Helper: detect punctuation characters in a string using Unicode category.


def _find_punctuations(text: str, allowed: set = None) -> List[str]:
    allowed = allowed or set()
    puncts = []
    for ch in text:
        if ch in allowed:
            continue
        if unicodedata.category(ch).startswith("P"):
            puncts.append(ch)
    return puncts


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Constraint: The response must conclude with the phrase "Days: [number]" where [number] is the calculated difference in days.

    Validator interpretation for reliability under simultaneous constraints:
    - The ending phrase must identify the day difference in the exact final line using the keyword 'Days' followed by the number.
    - To allow compatibility with the separate punctuation constraint, the safest compliant form is: "Days <integer>" (with one space, no punctuation).
    - We validate the final line to ensure it contains 'Days' and a non-negative integer, with no extra trailing content.
    - We do not validate the correctness of the number itself against any events; only the structural requirement.
    """
    ending = _get_ending_line(response)
    if not ending:
        return (
            False,
            "Your final response is empty or lacks a last line. End your output with a single final line containing the word 'Days' followed by a space and a non-negative integer, e.g., 'Days 123'. Do not add any text after that final line."
        )

    # Accept both "Days 123" and "Days: 123" structurally for identifier presence,
    # but recommend the punctuation-free variant in the guidance.
    m = re.fullmatch(r"Days(?:\s*:)?\s*(\d+)", ending)
    if not m:
        # Provide targeted guidance depending on common mistakes
        if not ending.startswith("Days"):
            return (
                False,
                "The final line must start with 'Days' (capital D, lowercase ays). Replace your last line with: 'Days <number>' where <number> is a non-negative integer. Example: 'Days 123'. Do not include any extra words before or after."
            )
        # It starts with Days but does not have a valid integer afterwards.
        # Detect if it has a negative sign, decimal, or non-digit characters.
        after = ending[len("Days"):].strip()
        if not after:
            return (
                False,
                "After 'Days' you must include a non-negative integer. Use exactly one space after 'Days' and then digits only. Example: 'Days 123'."
            )
        # If the integer part includes anything but digits, direct correction:
        return (
            False,
            "The ending phrase must present a non-negative integer after 'Days'. Use digits only (no signs, commas, periods, or words). Correct format example: 'Days 123'. Ensure this is the last line with no additional content."
        )

    # Success: identifiers present and a numeric value captured.
    # Provide actionable confirmation and reminders.
    return (
        True,
        "Valid: your ending line identifies the day count with 'Days' followed by a non-negative integer. Ensure this is the very last line with no extra content. For maximum compatibility with the punctuation rule, prefer 'Days <integer>' without any punctuation (e.g., 'Days 123')."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    ending = _get_ending_line(response)
    if not ending:
        return (
            False,
            "Your response has no final line to validate. End your output with the final line formatted as 'Days: <integer>' or 'Days <integer>'."
        )

    # 关键：允许冒号
    puncts = _find_punctuations(ending, allowed=ALLOWED_ENDING_PUNCT)

    if puncts:
        unique_puncts = []
        seen = set()
        for p in puncts:
            if p not in seen:
                seen.add(p)
                unique_puncts.append(p)
        found_list = " ".join(unique_puncts)
        return (
            False,
            f"The ending phrase contains disallowed punctuation characters: {found_list}. "
            "Remove all punctuation except ':' (or '：'). Correct examples: 'Days 123' or 'Days: 123'. "
            "Do not add any text after it."
        )

    return (
        True,
        "Valid: the ending phrase contains no disallowed punctuation (':' is allowed)."
    )

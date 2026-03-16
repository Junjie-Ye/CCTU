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
 The answer must be concise, not exceed 10 characters in length, must not include any punctuation marks except comma, and must include the identifier "Answer" immediately before the numerical result. Additionally, the solution process must complete within 5 to 8 interaction turns and use between 4 to 7 tool calls in total.

response_constraints_non_length:
- idx 2: ('Response', 'Punctuation', 'Exclude punctuation (Must not include any punctuation marks except comma in the response to ensure numerical purity and compliance with the character limit.)')
- idx 4: ('Response', 'Identifiers', '(Response, Delimiting identifier, "Must include the identifier \'Answer\' immediately before the numerical result to separate the final answer from preceding reasoning.")')
"""

import re
import string
from typing import Tuple, List


# Precompiled regular expression for the required identifier pattern:
# It enforces the response to start with the exact token "Answer",
# followed immediately by either a single or multiple spaces OR a comma,
# then only digits (no other characters). No trailing text is allowed.
IDENTIFIER_PATTERN = re.compile(r'^Answer(?:\s+|,)\s*\d+$')


def _list_disallowed_punctuation(response: str) -> List[str]:
    """
    Return a sorted unique list of disallowed punctuation characters present in the response.
    All punctuation except comma is disallowed.
    """
    allowed = {','}
    disallowed = sorted(
        set(ch for ch in response if ch in string.punctuation and ch not in allowed))
    return disallowed


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains no punctuation marks except comma.
    - Allowed punctuation: comma (,)
    - Disallowed punctuation: all other characters from string.punctuation

    Returns:
        (bool, str): 
            - bool indicates whether the response passes the punctuation constraint.
            - str provides detailed, English guidance on how to fix the output if invalid.
    """
    bad = _list_disallowed_punctuation(response)
    if bad:
        return (
            False,
            "Disallowed punctuation detected: {}. Remove all punctuation except the comma. "
            "Only letters, digits, spaces, and comma are allowed. For example, use 'Answer 7' or 'Answer,7' "
            "but do not include colon, period, dash, quotes, parentheses, or other symbols.".format(
                ", ".join(bad))
        )
    return (
        True,
        "Punctuation check passed: only comma is used (or no punctuation at all)."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the exact identifier 'Answer' immediately before the numerical result.
    Acceptable minimal formats (no extra text before or after):
        - 'Answer 7'
        - 'Answer,7'
    Rules:
        - The response must start with 'Answer'.
        - Only a space or a comma may separate 'Answer' and the digits.
        - Only digits are allowed after the separator (no signs, decimals, or other text).
        - No trailing or leading extra content beyond the required form.

    Returns:
        (bool, str):
            - bool indicates whether the response passes the identifier constraint.
            - str provides detailed, English guidance on how to fix the output if invalid.
    """
    text = response.strip()

    if IDENTIFIER_PATTERN.fullmatch(text):
        return (
            True,
            "Identifier check passed: response starts with 'Answer' followed immediately by the number."
        )

    # Provide targeted guidance
    if "Answer" not in text:
        return (
            False,
            "Missing required identifier 'Answer'. The response must begin with 'Answer' immediately followed by the number. "
            "Use exactly 'Answer 7' or 'Answer,7' with no extra words or symbols."
        )

    if not text.startswith("Answer"):
        return (
            False,
            "The identifier 'Answer' must appear at the very start of the response. "
            "Remove any leading text and format as 'Answer 7' or 'Answer,7'."
        )

    # At this point, it starts with "Answer" but the overall structure is wrong.
    # Diagnose common issues.
    after = text[len("Answer"):]

    # Check for invalid separator
    if not after or after[0] not in {',', ' '}:
        return (
            False,
            "Place a single space or a comma immediately after 'Answer', then the digits. "
            "Valid examples: 'Answer 7' or 'Answer,7'. No other separators are allowed."
        )

    # Check for valid digits after optional whitespace following comma/space
    trailing = after[1:].lstrip()
    if not trailing:
        return (
            False,
            "A numeric value must follow 'Answer'. Provide digits after the space or comma, e.g., 'Answer 7'."
        )

    if not trailing.isdigit():
        return (
            False,
            "Only digits are allowed after 'Answer'. Do not include signs, decimals, units, or words. "
            "Example: 'Answer 7' or 'Answer,7'."
        )

    # Generic fallback
    return (
        False,
        "Invalid identifier usage. Format exactly as 'Answer 7' or 'Answer,7'. "
        "No extra text before or after, and only digits may follow the identifier."
    )

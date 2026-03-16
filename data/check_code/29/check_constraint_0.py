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
 The answer must end with a period and must not contain any other punctuation marks. Additionally, you are allowed to make at most 2 interaction turns to find the answer. Ensure your final response is between 50 and 100 characters in length, maintaining conciseness and completeness. Your response must also begin with the phrase "Reelection Date:".

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period.)')
- idx 3: ('Response', 'Identifiers', "Start identifier (The agent's response must begin with the phrase 'Reelection Date:').")
"""

import re
from typing import Tuple

# Helper utilities
_PREFIX = "Reelection Date:"


def _last_non_space_char(s: str) -> str:
    """Return the last non-whitespace character in s, or empty string if none."""
    for ch in reversed(s):
        if not ch.isspace():
            return ch
    return ""


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate the punctuation constraint:
    - The response must end with a period '.' (considering trailing whitespace).
    Returns:
        (is_valid, message)
    """
    if not isinstance(response, str):
        return False, "Response must be a string."

    trimmed_last = _last_non_space_char(response)
    if trimmed_last != ".":
        return (
            False,
            "Your final response must end with a period. Ensure the last non-space character is '.'."
        )

    return True, "Punctuation is valid: response ends with a period."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the identifiers constraint:
    - The response must begin with the exact phrase 'Reelection Date:' (case-sensitive).
    Returns:
        (is_valid, message)
    """
    if not isinstance(response, str):
        return False, "Response must be a string."

    if response.startswith(_PREFIX):
        return True, "Identifier is valid: response starts with 'Reelection Date:'."

    if response.lstrip().startswith(_PREFIX):
        leading_ws_len = len(response) - len(response.lstrip())
        return (
            False,
            "Remove leading whitespace so the response starts at position 0 with the exact phrase 'Reelection Date:'."
            if leading_ws_len > 0 else
            "Start the response with the exact phrase 'Reelection Date:'."
        )

    return (
        False,
        "Begin the response with the exact phrase 'Reelection Date:' including capitalization and the colon, with no text before it."
    )

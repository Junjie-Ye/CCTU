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
 Your answer must end with a period to ensure proper sentence closure. Additionally, you may make at most 5 tool calls in total across all interaction turns, and the game_release_date_finder tool may be used at most 2 times during the process. The response must explicitly include a hyphen.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'Ending punctuation (Must end the response with a period to ensure proper sentence closure.)')
- idx 3: ('Response', 'Identifiers', 'Must include a hyphen in the response')
"""

from typing import Tuple

# Helper utilities


def _last_non_whitespace_char(s: str) -> str:
    """Return the last non-whitespace character of s, or empty string if none."""
    i = len(s) - 1
    while i >= 0 and s[i].isspace():
        i -= 1
    return s[i] if i >= 0 else ""


def _contains_ascii_hyphen(s: str) -> bool:
    """Return True if the ASCII hyphen-minus '-' appears anywhere in the string."""
    return '-' in s


def _contains_en_or_em_dash(s: str) -> bool:
    """Check for en dash or em dash presence."""
    return ('–' in s) or ('—' in s)


# Constraint: punctuation -> Must end the response with a period '.'
def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' as the final non-whitespace character.
    Returns:
        (is_valid, message)
        - message is detailed English guidance to fix the output if invalid.
    """
    last_char = _last_non_whitespace_char(response)
    if last_char == "":
        return (
            False,
            "The response is empty or only whitespace. Provide a complete answer and ensure the final non-whitespace character is a period '.'. For example, end the last sentence like: '... This is the conclusion.'."
        )
    if last_char != '.':
        return (
            False,
            "Your response must end with a period '.' as the final non-whitespace character. Append a period to the very end so nothing comes after it (e.g., 'Summary of findings.'). Avoid ending with other punctuation like '!' or '?'."
        )
    return (
        True,
        "Punctuation constraint satisfied: the response ends with a period '.' as the final non-whitespace character."
    )


# Constraint: identifiers -> Must include a hyphen '-'
def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least one ASCII hyphen '-' somewhere in the text.
    Returns:
        (is_valid, message)
        - message is detailed English guidance to fix the output if invalid.
    """
    if not response or response.strip() == "":
        return (
            False,
            "The response is empty or only whitespace. Include content and ensure it contains at least one ASCII hyphen '-'. For example: 'Key takeaway - final result.'"
        )

    if _contains_ascii_hyphen(response):
        return (
            True,
            "Identifier constraint satisfied: the response contains at least one ASCII hyphen '-'."
        )

    dash_hint = ""
    if _contains_en_or_em_dash(response):
        dash_hint = " You used an en dash '–' or em dash '—'. Replace it with the ASCII hyphen '-' or add a hyphen elsewhere."

    return (
        False,
        "The response must include at least one ASCII hyphen '-'. Insert a hyphen between words or clauses, for example: 'Plan - actions.' or 'Summary - details.'"
        + dash_hint
    )

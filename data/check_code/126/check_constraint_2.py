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
 You must obtain all information by calling the provided tools and not by answering the question directly. If a tool call fails, you must analyze the error, correct its parameters, and retry until success. Additionally, you must invoke between 1 and 2 unique tool types simultaneously in at least one interaction turn, but must not invoke more than 2 unique tool types simultaneously in any turn. The total number of tool calls must be between 2 and 3 (inclusive). Your final response must end with the phrase 'Based on historical records.' to indicate the source of the information.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', '("Response", "End identifier", "The agent\'s final response must end with the phrase \'Based on historical records.\' to indicate the source of the information.")')
"""

from typing import Tuple
import re

REQUIRED_END_PHRASE = "Based on historical records."


def _tail_snippet(text: str, n: int = 80) -> str:
    """
    Return the last n visible characters of text (after stripping right-side whitespace),
    to help users see what the response currently ends with.
    """
    trimmed = text.rstrip()
    return trimmed[-n:] if len(trimmed) > n else trimmed


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends exactly with the required end identifier:
    'Based on historical records.' (case-sensitive, includes the final period).

    Returns:
        (bool, str): 
            - bool indicates whether the constraint is satisfied.
            - str provides a detailed, English explanation and corrective guidance.
    """
    if response is None:
        return (
            False,
            "The response is empty. It must end exactly with: 'Based on historical records.' "
            "Add this phrase as the final characters of your answer (including the period), "
            "with no text after it."
        )

    trimmed = response.rstrip()
    required = REQUIRED_END_PHRASE

    # Exact match at the very end (after trimming trailing whitespace)
    if trimmed.endswith(required):
        return (
            True,
            "Pass: The response ends with the required phrase exactly, including the final period."
        )

    # Diagnose common mistakes
    tail = _tail_snippet(response)

    # 1) Missing final period
    # ends with "Based on historical records"
    if trimmed.endswith(required[:-1]):
        return (
            False,
            "The response ends with 'Based on historical records' but is missing the final period. "
            "Change the ending to exactly: 'Based on historical records.' "
            "Ensure there is no extra text, punctuation, or quotes after the period. "
            f"Current ending: '{tail}'"
        )

    # 2) Correct phrase present but not at the end
    if required in trimmed and not trimmed.endswith(required):
        return (
            False,
            "The required phrase appears in the response but not at the very end. "
            "Move the phrase to the end so the response finishes exactly with: 'Based on historical records.' "
            "Remove any characters after it (no trailing quotes, footnotes, or extra punctuation). "
            f"Current ending: '{tail}'"
        )

    # 3) Case-insensitive match (wrong casing or punctuation variants)
    if trimmed.lower().endswith(required.lower()):
        return (
            False,
            "The ending phrase must match exactly in case and punctuation. "
            "Replace the ending with: 'Based on historical records.' "
            "Do not add any characters after it. "
            f"Current ending: '{tail}'"
        )

    # 4) Phrase followed by extra characters (detect anywhere near the end)
    pattern = re.compile(re.escape(required) + r".+$")
    if pattern.search(trimmed):
        return (
            False,
            "There are extra characters after the required ending phrase. "
            "The response must end exactly with: 'Based on historical records.' "
            "Remove any trailing quotes, emojis, spaces, or notes after the period. "
            f"Current ending: '{tail}'"
        )

    # 5) Phrase absent entirely
    return (
        False,
        "The response does not end with the required phrase. "
        "Append the exact text at the very end (including the period and correct casing): "
        "'Based on historical records.' "
        "Ensure there is no text after it (no trailing punctuation or quotes). "
        f"Current ending: '{tail}'"
    )

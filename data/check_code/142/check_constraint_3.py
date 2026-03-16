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
 If the agent intends to use the historical_event_date_finder, it must execute two distinct function calls within a single action step. Additionally, the historical_event_date_finder tool may be called at most 2 times during the entire task execution. Your final response must start with the exact phrase "The number of days is" and end with a period.

response_constraints_non_length:
- idx 3: ('Response', 'Identifiers', 'The agent\'s response must start with the exact phrase "The number of days is".')
- idx 4: ('Response', 'Punctuation', "The agent's response must end with a period.")
"""

from typing import Tuple

# Constants for constraints
START_PHRASE = 'The number of days is'
REQUIRED_END_PUNCT = '.'


def _last_non_whitespace_char(s: str) -> str:
    """
    Return the last non-whitespace character in the string, or empty string if none.
    """
    i = len(s) - 1
    while i >= 0 and s[i].isspace():
        i -= 1
    return s[i] if i >= 0 else ''


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response starts with the exact phrase: 'The number of days is'.
    - The check is case-sensitive and must occur at character position 0 (no leading text or whitespace).
    """
    if response.startswith(START_PHRASE):
        return True, "Valid: response starts with the exact required phrase."
    # Build a detailed error message
    if START_PHRASE in response:
        idx = response.find(START_PHRASE)
        return (
            False,
            "Invalid: the response must start at position 0 with the exact phrase "
            f"'{START_PHRASE}'. Detected the phrase at index {idx}, which means there is "
            "leading content or whitespace. Remove any leading text or whitespace so the "
            f"very first characters are exactly: '{START_PHRASE}'."
        )
    # Provide hints if casing or spacing might be wrong
    normalized_response = response.strip()
    if normalized_response.lower().startswith(START_PHRASE.lower()):
        return (
            False,
            "Invalid: the response begins with a case-insensitive match but not the exact phrase. "
            f"Use the exact casing and spacing: '{START_PHRASE}' as the first characters of the response, "
            "with no preceding whitespace or text."
        )
    return (
        False,
        "Invalid: the response must start with the exact phrase "
        f"'{START_PHRASE}' as the very first characters. Insert this phrase at the beginning "
        "with correct casing and spacing, and remove any leading content."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.'.
    - Trailing whitespace after the period is allowed, but the last non-whitespace character must be '.'.
    """
    last_char = _last_non_whitespace_char(response)
    if last_char == REQUIRED_END_PUNCT:
        return True, "Valid: response ends with a period as required."
    if last_char == '':
        return (
            False,
            "Invalid: the response is empty or whitespace-only. Provide a complete response that ends "
            "with a period '.' as the final non-whitespace character."
        )
    return (
        False,
        "Invalid: the response must end with a period '.' as the final non-whitespace character. "
        "Add a '.' at the end (before any trailing spaces if present)."
    )

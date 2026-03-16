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
 Your response must begin with the phrase "The local flower is" followed by the identified flower name in a single sentence, must be at most 15 words in length to ensure conciseness, and must end with a period.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'The response must begin with the phrase "The local flower is" followed by the identified flower name in a single sentence.')
- idx 2: ('Response', 'Punctuation', '(Response, Punctuation, "Ending punctuation (.) must be used at the end of the response")')
"""

import re
from typing import Tuple

# Helper regex patterns
SENTENCE_ENDERS_PATTERN = re.compile(r'[.!?]')
MULTI_PERIOD_ENDING_PATTERN = re.compile(
    r'\.\.+$')  # matches "..." or ".." at the end

PHRASE = "The local flower is"


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the identifiers constraint:
    - The response must begin with the exact phrase "The local flower is".
    - The phrase must be immediately followed by a space and then the flower name.
    - The content must be a single sentence (i.e., no additional sentence terminators before the end).
    Note: This function does NOT enforce the final period (.) — that is validated by validate_punctuation.
    """
    if response is None or not isinstance(response, str) or response.strip() == "":
        return (
            False,
            "Response is empty. Start with 'The local flower is' followed by the flower name in one sentence."
        )

    text = response.strip()

    # 1) Must start with the exact phrase (case-sensitive)
    if not text.startswith(PHRASE):
        return (
            False,
            "Response must start exactly with 'The local flower is' (case-sensitive) with no preface."
        )

    # 2) Must have a space after the phrase and then a non-empty flower name
    if len(text) == len(PHRASE):
        return (
            False,
            "Add a space and the flower name after 'The local flower is'."
        )
    if text[len(PHRASE)] != " ":
        return (
            False,
            "Insert a single space after 'The local flower is' before the flower name."
        )

    remainder = text[len(PHRASE) + 1:]  # text after the phrase and a space

    # 3) Flower name must contain letters (avoid empty or purely punctuation)
    if not re.search(r"[A-Za-z]", remainder):
        return (
            False,
            "Provide a valid flower name (use alphabetic characters) immediately after the phrase."
        )

    # 4) Single sentence check:
    #    - Allow at most one sentence terminator, which must be at the very end if present.
    ender_positions = [m.start()
                       for m in SENTENCE_ENDERS_PATTERN.finditer(text)]
    if len(ender_positions) > 1:
        return (
            False,
            "Use a single sentence only. Remove extra sentence terminators like '.', '!', or '?'."
        )
    if len(ender_positions) == 1 and ender_positions[0] != len(text) - 1:
        return (
            False,
            "End the sentence with a single terminator at the very end; remove any earlier '.', '!', or '?'."
        )

    return True, "Identifiers constraint satisfied."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates the punctuation constraint:
    - Ending punctuation (.) must be used at the end of the response.
    - The period must be the final character (no trailing spaces).
    - Avoid ellipses (e.g., '...' or '..') — use exactly one period.
    """
    if response is None or not isinstance(response, str) or response.strip() == "":
        return (
            False,
            "Response is empty. End the response with a single period '.' as the final character."
        )

    raw = response
    text = response.strip()

    # Must end with a period after trimming whitespace
    if not text.endswith("."):
        return (
            False,
            "End the response with exactly one period '.' (no other ending punctuation)."
        )

    # Disallow ellipses / multiple periods at the end
    if MULTI_PERIOD_ENDING_PATTERN.search(text):
        return (
            False,
            "Use exactly one period at the end (avoid '...' or multiple periods)."
        )

    # No trailing spaces after the period in the original response
    if raw != text:
        # Original response had trailing/leading whitespace; require none after the final period
        # Specifically ensure last non-space char is '.'
        if not raw.rstrip().endswith("."):
            return (
                False,
                "Ensure the last non-space character is a single period '.' at the end."
            )

    return True, "Punctuation constraint satisfied."

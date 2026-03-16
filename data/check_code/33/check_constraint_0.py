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
 The answer must begin with the phrase 'The conviction date for Radislav Krstić is' and must be between 40 and 60 characters in length.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "The response must begin with the phrase 'The conviction date for Radislav Krstić is'")
"""

from typing import Tuple
import unicodedata

# Helper: remove diacritics for fuzzy comparisons


def _strip_diacritics(s: str) -> str:
    if s is None:
        return ""
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")

# Helper: find index of first difference between two strings


def _first_diff_index(a: str, b: str) -> int:
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            return i
    return min(len(a), len(b)) if len(a) != len(b) else -1


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response begins exactly with the required phrase
    'The conviction date for Radislav Krstić is' (case- and accent-sensitive),
    with no leading whitespace, punctuation, or other text.
    """
    expected_phrase = "The conviction date for Radislav Krstić is"

    if not isinstance(response, str):
        return (
            False,
            "The response must be a string. Provide a string that begins exactly with: "
            f"{expected_phrase}"
        )

    if response.startswith(expected_phrase):
        return (
            True,
            "Pass: The response begins with the exact required phrase."
        )

    # Empty or too short
    if not response:
        return (
            False,
            "Your response is empty. Start the response exactly with: "
            f"'{expected_phrase}' (no leading spaces or other characters)."
        )

    # Leading whitespace check
    if response.strip().startswith(expected_phrase) and not response.startswith(expected_phrase):
        return (
            False,
            "Remove any leading whitespace. The very first character of the response must be 'T' "
            f"and the response must begin exactly with: '{expected_phrase}'."
        )

    # Phrase appears later in the string
    if expected_phrase in response and not response.startswith(expected_phrase):
        idx = response.find(expected_phrase)
        return (
            False,
            f"The required phrase appears at index {idx}, but it must start at index 0. "
            f"Move it to the beginning so the response starts exactly with: '{expected_phrase}'. "
            "Do not prepend any other text, tags, or punctuation."
        )

    # Compare first segment for case/diacritics guidance
    seg = response[:len(expected_phrase)]
    if seg.lower() == expected_phrase.lower() and seg != expected_phrase:
        diff_i = _first_diff_index(seg, expected_phrase)
        return (
            False,
            "The response starts with a nearly correct phrase but the casing and/or diacritics "
            f"do not match at or near position {diff_i}. Use the exact phrase with correct "
            f"capitalization and the character 'ć' (c-acute): '{expected_phrase}'."
        )

    # Diacritics-only mismatch (e.g., 'c' vs 'ć')
    if _strip_diacritics(seg).lower() == _strip_diacritics(expected_phrase).lower() and seg != expected_phrase:
        diff_i = _first_diff_index(seg, expected_phrase)
        return (
            False,
            "The response begins with a visually similar phrase but is missing required diacritics "
            f"(likely at position {diff_i}). Use the exact character 'ć' in 'Krstić' and match the "
            f"phrase exactly: '{expected_phrase}'."
        )

    # Generic failure message
    return (
        False,
        "The response must begin exactly with the phrase: "
        f"'{expected_phrase}'. Do not add any leading spaces, punctuation, or text such as "
        "[THOUGHT]/[ACTION]. Keep the exact spelling, capitalization, and diacritics."
    )

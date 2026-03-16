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
 Your response must be between 50 and 150 characters in length, including spaces and punctuation. Additionally, you may call the `historical_event_tool` at most 2 times during the task. Ensure that your final answer ends with a period.

response_constraints_non_length:
- idx 2: ('Response', 'Punctuation', "The agent's final response must end with a period.")
"""

from typing import Tuple

# Helper functions


def _last_non_whitespace_char(s: str):
    """Return the last non-whitespace character of s, or None if none exists."""
    if not s:
        return None
    trimmed = s.rstrip()
    if not trimmed:
        return None
    return trimmed[-1]


def _describe_char(c: str) -> str:
    """Return a human-readable description of a single character."""
    if c is None:
        return "none (empty or whitespace-only response)"
    named = {
        '.': "'.' (ASCII period)",
        '。': "'。' (CJK full stop)",
        '!': "'!'",
        '?': "'?'",
        '"': "'\"' (quote)",
        "'": "\"'\" (apostrophe)",
        '...': "'...' (ellipsis character)",
    }
    return named.get(c, f"'{c}' (U+{ord(c):04X})")

# Constraint validator: punctuation


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period.
    Requirement: The agent's final response must end with a period.
    We enforce that the last non-whitespace character is an ASCII '.'.
    """
    last_char = _last_non_whitespace_char(response)
    if last_char == '.':
        return True, "Valid: the last non-whitespace character is an ASCII period '.'."
    # Not valid
    detail = _describe_char(last_char)
    return (
        False,
        (
            "Invalid punctuation: the final answer must end with a single ASCII period '.' "
            "as the last non-whitespace character. "
            f"Currently ends with {detail}. "
            "Fix by trimming any trailing spaces/newlines and appending exactly one '.' at the end. "
            "Do not add quotes or other punctuation after the period, and do not change the content."
        ),
    )

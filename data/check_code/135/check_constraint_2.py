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
 You must use the available tools to find the answer, and your solution must involve between 2 and 5 interaction turns, inclusive. Additionally, you are limited to at most 2 calls per unique tool type for this task. Your final answer must use the delimiter "###" to clearly separate the two results in the response.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', 'The final answer must use the delimiter "###" to clearly separate the two results in the response.')
"""

import re
from typing import Tuple, List

# Precompiled regex to find the exact delimiter "###" not embedded in longer hash runs.
# (?<!#) ensures no preceding '#', (?!#) ensures no following '#', so only exactly three hashes match.
_DELIMITER_PATTERN = re.compile(r'(?<!#)###(?!#)')


def _find_delimiter_matches(text: str) -> List[re.Match]:
    """Return all matches of the exact '###' delimiter in the text."""
    return list(_DELIMITER_PATTERN.finditer(text))


def _line_number_at(text: str, index: int) -> int:
    """Return 1-based line number at a given string index."""
    return text.count('\n', 0, index) + 1


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer uses the delimiter '###' to clearly separate two results.
    Requirements interpreted:
    - There must be exactly one delimiter consisting of exactly three hash characters: '###'.
    - The delimiter should separate exactly two non-empty sections (before and after).
    - To maximize clarity, placing the delimiter on its own line is recommended (not strictly required).
    """
    matches = _find_delimiter_matches(response)
    count = len(matches)

    if count == 0:
        return (
            False,
            "Missing delimiter. Add exactly one delimiter consisting of three hash characters: '###'. "
            "Place it between two non-empty result sections. Recommended layout:\n"
            "<result 1>\n###\n<result 2>\n"
            "Do not use more than one '###' and avoid longer hash runs like '####'."
        )

    if count > 1:
        lines = [str(_line_number_at(response, m.start())) for m in matches]
        return (
            False,
            f"Too many delimiters: found {count} occurrences of '###' at lines {', '.join(lines)}. "
            "Keep exactly one '###' to separate the two results. Remove all extra occurrences. "
            "Ensure there are exactly two non-empty sections: one before and one after the single delimiter."
        )

    # Exactly one delimiter found
    m = matches[0]
    before = response[:m.start()]
    after = response[m.end():]

    if not before.strip() and not after.strip():
        return (
            False,
            "Both sections around the '###' delimiter are empty. Provide two non-empty result sections: "
            "place meaningful content before and after the single '###' delimiter."
        )
    if not before.strip():
        return (
            False,
            "The section before the '###' delimiter is empty. Add the first result before the delimiter. "
            "Example:\n<result 1>\n###\n<result 2>"
        )
    if not after.strip():
        return (
            False,
            "The section after the '###' delimiter is empty. Add the second result after the delimiter. "
            "Example:\n<result 1>\n###\n<result 2>"
        )

    # Optional clarity check: whether the delimiter is on its own line (recommended).
    # We do not fail if it's inline; we only provide success with a note.
    on_its_own_line = False
    # Determine line boundaries around the delimiter
    prev_nl = response.rfind('\n', 0, m.start())
    next_nl = response.find('\n', m.end())
    left_segment = response[prev_nl + 1: m.start()
                            ] if prev_nl != -1 else response[:m.start()]
    right_segment = response[m.end(): next_nl] if next_nl != - \
        1 else response[m.end():]
    if left_segment.strip() == "" and right_segment.strip() == "":
        on_its_own_line = True

    if on_its_own_line:
        return (
            True,
            "Valid: exactly one '###' delimiter found with two non-empty sections, and the delimiter is on its own line."
        )
    else:
        return (
            True,
            "Valid: exactly one '###' delimiter found with two non-empty sections. "
            "For maximal clarity, consider placing the delimiter on its own line, e.g.:\n<result 1>\n###\n<result 2>"
        )

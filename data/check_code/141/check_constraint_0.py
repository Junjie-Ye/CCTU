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
 Your response must include the phrases "• Human: [X]" and "• Shark: [Y]" as delimiters before stating the difference. The solution must involve at least two separate tool calls to retrieve information about human and shark teeth. You must not call any individual tool more than twice during this process. You must complete this task within at most 3 interaction turns, including all tool calls and final response.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "Must include the phrases '• Human: [X]' and '• Shark: [Y]' as delimiters before stating the difference.")
"""

import re
from typing import Tuple, Optional, Match

# Precompiled regex patterns for the required identifier phrases.
# They require the exact bullet "•", exact tokens "Human" and "Shark",
# and a bracketed payload like [X] / [Y] with any non-bracket, non-newline content.
HUMAN_PATTERN = re.compile(
    r'•\s*Human:\s*\[([^\[\]\n]+)\]', flags=re.MULTILINE)
SHARK_PATTERN = re.compile(
    r'•\s*Shark:\s*\[([^\[\]\n]+)\]', flags=re.MULTILINE)


def _find_first(pattern: re.Pattern, text: str) -> Optional[Match]:
    """Return the first regex match if present, else None."""
    return pattern.search(text)


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains the required identifier phrases:
    - "• Human: [X]"
    - "• Shark: [Y]"
    ...and that these delimiter lines appear before stating the difference.

    Rules enforced:
    1) The exact bullet character '•' must be used.
    2) The exact tokens "Human" and "Shark" must be used with a colon.
    3) A bracketed payload must be present, e.g., [32] or [X].
    4) Both delimiter lines must appear before the difference statement.
       - If a line containing the word "difference" exists, it must appear after both delimiters.
       - If "difference" is not present, there must still be some non-empty content after both delimiters,
         ideally indicating the numerical difference (e.g., digits).
    """
    human_m = _find_first(HUMAN_PATTERN, response)
    shark_m = _find_first(SHARK_PATTERN, response)

    missing = []
    if not human_m:
        missing.append("• Human: [X]")
    if not shark_m:
        missing.append("• Shark: [Y]")

    if missing:
        return (
            False,
            "Identifiers missing or malformed. Your response must include both delimiter phrases exactly as:\n"
            "• Human: [X]\n"
            "• Shark: [Y]\n"
            "- Use the U+2022 bullet '•' at the start of each line (not '-', '*', or '• ' with missing bullet).\n"
            "- Keep 'Human' and 'Shark' capitalized exactly, followed by a colon.\n"
            "- Wrap the value in square brackets, e.g., [32].\n"
            f"Missing/incorrect: {', '.join(missing)}"
        )

    # Determine ordering and ensure anything that states the difference appears after both.
    last_delim_end = max(human_m.end(), shark_m.end())
    tail = response[last_delim_end:].strip()

    # If the response contains a "difference" statement, ensure it appears after both delimiters.
    diff_idx = response.lower().find("difference")
    if diff_idx != -1 and diff_idx < last_delim_end:
        return (
            False,
            "The difference statement appears before at least one of the required delimiter lines. "
            "Move the two lines with the exact phrases\n"
            "• Human: [X]\n"
            "• Shark: [Y]\n"
            "so they appear before the difference statement."
        )

    # If "difference" is not explicitly present, ensure there is still meaningful content after the delimiters.
    if not tail:
        return (
            False,
            "After the two delimiter lines, you must state the numerical difference between X and Y. "
            "Add a line after both delimiters, for example:\n"
            "Difference: 18 (Shark - Human)"
        )

    # Optionally, nudge toward numeric evidence in the tail if "difference" keyword not present.
    if diff_idx == -1 and not re.search(r'\d', tail):
        return (
            False,
            "After the two delimiter lines, explicitly state the numerical difference between X and Y. "
            "Include a number (e.g., digits) in that statement. Example:\n"
            "Difference: 18 (Shark - Human)"
        )

    return (
        True,
        "Identifiers constraint satisfied: both '• Human: [X]' and '• Shark: [Y]' are present and appear before the difference."
    )

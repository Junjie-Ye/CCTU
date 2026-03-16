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
 Your solution must use between 7 and 11 tool calls to ensure sufficient information retrieval while preventing excessive execution, each tool can be called at most 2 times during the task, and the response must conclude with the identifier "END OF ANSWER"

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', '(Main Category, Response, End identifier: "The response must conclude with the identifier \'END OF ANSWER\' to provide a clear and consistent ending.")')
"""

from typing import Tuple
import re

IDENTIFIER = "END OF ANSWER"


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the exact end identifier: 'END OF ANSWER'.

    Rules:
    - The final non-whitespace characters of the response must be exactly: END OF ANSWER
    - Case must match exactly (uppercase).
    - No quotes, brackets, punctuation, or any other characters may follow the identifier.
    - The identifier may be on a new line; trailing whitespace after it is not allowed (it must be the final non-whitespace content).
    """
    if response is None:
        return (
            False,
            "The response is empty. Append the exact identifier END OF ANSWER as the final non-whitespace content (e.g., '...\\nEND OF ANSWER')."
        )

    trimmed = response.rstrip()  # remove only trailing whitespace for end-checks
    # 1) Exact, case-sensitive match at the very end
    if trimmed.endswith(IDENTIFIER):
        return (
            True,
            "Valid: the response correctly concludes with the exact identifier END OF ANSWER as the final non-whitespace content."
        )

    # 2) If it ends with a quoted identifier like "END OF ANSWER" or 'END OF ANSWER'
    if trimmed.endswith(f"\"{IDENTIFIER}\"") or trimmed.endswith(f"'{IDENTIFIER}'"):
        return (
            False,
            "Do not quote the identifier. Remove the surrounding quotes so the final non-whitespace characters are exactly: END OF ANSWER"
        )

    # 3) If it ends with the identifier followed by punctuation (e.g., END OF ANSWER., END OF ANSWER!)
    punctuation_after_identifier = re.compile(
        rf"{re.escape(IDENTIFIER)}\s*[\.\!\?\:\;\)\]\}}]+$")
    if punctuation_after_identifier.search(trimmed):
        return (
            False,
            "Remove any punctuation after the identifier. The final non-whitespace characters must be exactly: END OF ANSWER"
        )

    # 4) Contains the identifier but not at the end
    pos = trimmed.find(IDENTIFIER)
    if pos != -1 and pos + len(IDENTIFIER) != len(trimmed):
        return (
            False,
            "Move the identifier to the very end and remove any trailing content. The final non-whitespace characters must be exactly: END OF ANSWER"
        )

    # 5) Case-insensitive presence at the end (wrong casing)
    if trimmed.lower().endswith(IDENTIFIER.lower()):
        return (
            False,
            "Use the exact casing. Replace the current ending with the uppercase identifier: END OF ANSWER"
        )

    # 6) Identifier appears elsewhere with wrong casing
    if re.search(r"end of answer", trimmed, re.IGNORECASE):
        return (
            False,
            "Position and casing are incorrect. Ensure the final non-whitespace characters are exactly: END OF ANSWER"
        )

    # 7) Identifier missing entirely
    return (
        False,
        "Append the exact identifier at the end. The final non-whitespace characters must be exactly: END OF ANSWER (e.g., '...\\nEND OF ANSWER')."
    )

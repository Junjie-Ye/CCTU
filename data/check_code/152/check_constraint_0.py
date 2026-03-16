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
Rank from earliest to latest: (a) the construction date of the architectural wonder located in the city with ancient aqueducts, (b) the publication year of the novel by the author known for exploring human nature in his works, and (c) the date the first manned spacecraft landed on the satellite facing our planet. You must complete this task within a maximum of 15 interaction turns to ensure efficiency. Additionally, your final response must be at least 150 characters in length to ensure sufficient detail and completeness. Furthermore, you must ensure that in any single interaction turn, you invoke at most 4 unique tool types simultaneously. Ensure that the final response ends with a period to maintain proper sentence closure.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', '(Response, Punctuation, Ending punctuation (The final response must end with a period to ensure proper sentence closure.))')
"""

from typing import Tuple

# Punctuation validator for response constraints.
# This module verifies that the final response ends with a period '.'.
# It returns a (bool, str) tuple where:
#  - bool indicates whether the response satisfies the punctuation constraint
#  - str provides detailed, English guidance on how to fix issues if invalid


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period '.' as the very last character.

    Args:
        response: The full response string produced by the agent.

    Returns:
        A tuple (is_valid, message). If invalid, the message explains exactly how to fix it.
    """
    if response is None:
        response = ""

    trimmed = response.rstrip()  # ignore trailing whitespace only
    if not trimmed:
        return (
            False,
            "The response is empty. Provide a complete final answer and ensure it ends with a period '.' as the last character without trailing whitespace."
        )

    last_char = trimmed[-1]
    if last_char == ".":
        return (
            True,
            "Punctuation requirement satisfied: the final character is a period '.'."
        )

    # Construct targeted feedback based on common trailing characters.
    if last_char in {"!", "?"}:
        reason = f"The last character is '{last_char}', not a period."
        fix = "Replace it with a period '.' so the very last character is '.'."
    elif last_char in {'"', "'", "”", "’", ")", "]", "}", ":", ";", ",", "—"}:
        reason = f"The last character is '{last_char}', not a period."
        fix = "Place a final '.' at the very end of the response after any closing quotes or brackets, with no characters or spaces following it."
    else:
        reason = f"The last character is '{last_char}', not a period."
        fix = "Append a period '.' to the end of the response and do not include any characters or spaces after it."

    return (
        False,
        f"{reason} The final response must end with a period to ensure proper sentence closure. {fix} Example ending: '...results.'"
    )

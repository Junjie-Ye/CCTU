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
 You must derive the answer using tool calls within a maximum of 3 interaction turns, ensure that the total number of tool calls executed across all interaction turns is between 1 and 3, and begin your final response with the exact phrase "The date is" to standardize the answer format.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', 'Start identifier (The agent\'s response must begin with the exact phrase "The date is" to standardize the opening of the answer.)')
"""

from typing import Tuple

REQUIRED_PREFIX = "The date is"


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the agent's response begins with the exact required start identifier.

    Constraint:
    - The response must begin with the exact phrase: "The date is"
      (case-sensitive, no leading characters or whitespace before it).

    Returns:
    - (True, message) if valid.
    - (False, detailed guidance) if invalid, with precise instructions to fix the output.
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string. Start it exactly with 'The date is' followed by the verified date, e.g., 'The date is 10 May 2007.'."
        )

    # Exact match at the very start
    if response.startswith(REQUIRED_PREFIX):
        return (
            True,
            "Valid: The response begins with the exact phrase 'The date is'. Keep this phrase at index 0 with the same casing and spacing."
        )

    # Leading whitespace before the correct phrase
    stripped_left = response.lstrip()
    if stripped_left.startswith(REQUIRED_PREFIX):
        leading_len = len(response) - len(stripped_left)
        return (
            False,
            f"The response has {leading_len} leading whitespace character(s) before the required opening. "
            "Remove all leading whitespace so the message begins exactly with 'The date is'. "
            "Example: 'The date is 10 May 2007.'."
        )

    # Correct words but incorrect casing or spacing in the first characters
    prefix_len = len(REQUIRED_PREFIX)
    candidate_prefix = response[:prefix_len]
    if candidate_prefix.lower() == REQUIRED_PREFIX.lower():
        return (
            False,
            "The response uses the right words but with incorrect casing or spacing. "
            "Start exactly with 'The date is' (case-sensitive, single spaces). "
            "Example: 'The date is 10 May 2007.'."
        )

    # Phrase appears later in the string, not at the beginning
    idx = response.find(REQUIRED_PREFIX)
    if idx > 0:
        return (
            False,
            f"The required opening phrase 'The date is' appears at position {idx}, but it must start at position 0. "
            "Move it to the very beginning with no preceding text or whitespace. "
            "Example: 'The date is 10 May 2007.'."
        )

    # Phrase missing entirely
    return (
        False,
        "The response does not start with the required opening phrase. "
        "Begin the message exactly with 'The date is' followed by the verified date, "
        "e.g., 'The date is 10 May 2007.'. No text or whitespace should precede the phrase."
    )

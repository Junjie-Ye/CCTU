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
 If you initiates the task with `countryside_distillery_locator`, it is strictly required to proceed with the following sequence: `business_locator` -> `distillery_spirit_identifier` -> `bartender_matcher` -> `individual_location_finder` -> `local_specialty_finder`. The solution must complete within at most 8 interaction turns, the `distillery_spirit_identifier` tool must not be called more than 3 times, and your final answer must end with a period.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The response must end with a period.')
"""

from typing import Tuple


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period, as required by the response constraints.
    - Success criterion: After trimming trailing whitespace, the very last character must be '.'.

    Returns:
        (is_valid, message)
        - is_valid: True if valid; False otherwise.
        - message: Detailed English guidance to correct the output if invalid.
    """
    if response is None:
        return (
            False,
            "The response is missing (None). Provide a final answer string whose last non-whitespace character is a period '.'."
        )

    trimmed = response.rstrip()
    if len(trimmed) == 0:
        return (
            False,
            "The response is empty. Provide a final answer that ends with a period '.' as the last non-whitespace character."
        )

    if trimmed.endswith("."):
        return (
            True,
            "Valid: The response ends with a period '.' after trimming trailing whitespace."
        )

    last_char = trimmed[-1]
    return (
        False,
        (
            f"The response does not end with a period. The last non-whitespace character is '{last_char}'. "
            "Revise the output so that the final character is a period '.'. "
            "Do not add extra spaces after the period. If the answer currently ends with other punctuation "
            "(e.g., '!', '?', quotation marks, or brackets), replace or move the period so it is the very last character."
        )
    )

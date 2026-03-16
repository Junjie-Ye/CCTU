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
 The answer must be concise and not exceed 200 characters. The `startup_identifier` must be called before `corporate_acquisition_finder`, and `corporate_acquisition_finder` must be called before `product_information_retriever`. The solution must use between 7 and 9 interaction turns, inclusive. Each of the tools `startup_identifier`, `corporate_acquisition_finder`, and `product_information_retriever` must be called at most once. The final answer must include the delimiter "[ANSWER]" before the landmark name to clearly indicate the answer section.

response_constraints_non_length:
- idx 4: ('Response', 'Identifiers', '(Main Category, Response, Delimiting identifier (The agent\'s response must include the delimiter "[ANSWER]" before the final landmark name to clearly indicate the answer section.))')
"""

import re
from typing import Tuple

# Identifier constraint validator
# Requirement: The response must include the exact delimiter "[ANSWER]" before the final landmark name.


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response includes the exact delimiter "[ANSWER]" before the landmark name.
    Returns:
        (bool, str): (is_valid, guidance_message_in_english)
    """
    if response is None:
        return (
            False,
            "Response is None. Provide a string containing the exact delimiter '[ANSWER]' followed by the landmark name."
        )

    delimiter = "[ANSWER]"
    count = response.count(delimiter)

    # Must contain the delimiter exactly once
    if count == 0:
        return (
            False,
            "Missing required identifier. Include the exact delimiter '[ANSWER]' (uppercase, with brackets) before the landmark name, e.g., '[ANSWER] Eiffel Tower'."
        )
    if count > 1:
        return (
            False,
            "Use the delimiter exactly once. Provide a single '[ANSWER]' followed by the exact landmark name, e.g., '[ANSWER] Eiffel Tower'. Remove any extra delimiters."
        )

    idx = response.find(delimiter)
    after = response[idx + len(delimiter):]

    # There must be some non-whitespace characters after the delimiter
    if not re.search(r"\S", after or ""):
        return (
            False,
            "The delimiter must be immediately followed by the landmark name. Add the landmark after '[ANSWER]', e.g., '[ANSWER] Eiffel Tower'."
        )

    # Check that the content after the delimiter looks like a landmark name (at least one letter)
    if not re.search(r"[A-Za-z]", after):
        return (
            False,
            "Ensure a valid landmark name follows the delimiter. Provide letters after '[ANSWER]', e.g., '[ANSWER] Golden Gate Bridge'."
        )

    # Optional guidance: suggest a space after the delimiter if absent (not strictly required, but clearer)
    if not after.startswith(" "):
        return (
            True,
            "Identifier is present and precedes the landmark. For clarity, place a single space after '[ANSWER]', e.g., '[ANSWER] Landmark Name'."
        )

    return (
        True,
        "Identifier '[ANSWER]' is correctly included before the landmark name."
    )

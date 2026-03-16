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
 If the agent intends to use the `chef_dish_associator` tool, it is strictly required to first call the `restaurant_locator` If the agent invokes both island_feature_locator and restaurant_locator, these tools must be executed simultaneously in a single action step. The total number of tool calls the agent can execute across all interaction turns must not exceed 15. At least two distinct tools must be invoked in at least one interaction turn. The response must end with a period to ensure proper sentence closure and also end with the phrase "Tourist comparison completed."

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period to ensure proper sentence closure.)')
- idx 4: ('Response', 'Identifiers', '(Response, End identifier, Must end with the phrase "Tourist comparison completed.")')
"""

import re
from typing import Tuple

# Constants for identifier checks
END_PHRASE = "Tourist comparison completed."
END_PHRASE_LOWER = END_PHRASE.lower()


def _rstrip_preserve(s: str) -> str:
    """
    Return the string with trailing whitespace removed.
    This is used to evaluate the 'final' visible character/phrase.
    """
    return s.rstrip()


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' (considering trailing whitespace).
    Returns:
      - (True, "OK: ...") if valid.
      - (False, "Detailed guidance...") if invalid.
    """
    trimmed = _rstrip_preserve(response)
    if len(trimmed) == 0:
        return (
            False,
            "The response is empty. Provide a complete answer that ends with a period '.' as the final non-whitespace character."
        )

    last_char = trimmed[-1]
    if last_char == '.':
        return (True, "OK: The response ends with a period '.' as required.")
    else:
        # Provide a targeted suggestion depending on the last visible punctuation
        if last_char in ['!', '?', ';', ':', ',', '...', '—', '-']:
            return (
                False,
                f"The final non-whitespace character is '{last_char}', not a period. Replace the final punctuation with a single period '.', e.g., '... {END_PHRASE}'."
            )
        else:
            return (
                False,
                "The response does not end with a period. Ensure the final non-whitespace character is a single period '.', e.g., end with '... Tourist comparison completed.'."
            )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the exact phrase:
      Tourist comparison completed.
    (case-sensitive, includes the period, and ignoring trailing whitespace).
    Returns:
      - (True, "OK: ...") if valid.
      - (False, "Detailed guidance...") if invalid.
    """
    trimmed = _rstrip_preserve(response)

    # Exact match at the end (case-sensitive, including the period)
    if trimmed.endswith(END_PHRASE):
        return (True, "OK: The response ends with the exact phrase 'Tourist comparison completed.'")

    # Common near-misses with targeted guidance:
    # 1) Phrase present but quoted at the very end
    if trimmed.endswith(f"\"{END_PHRASE}\"") or trimmed.endswith(f"'{END_PHRASE}'") or trimmed.endswith(f"`{END_PHRASE}`"):
        return (
            False,
            "Do not wrap the end phrase in quotes. Remove the surrounding quotes and end exactly with: Tourist comparison completed."
        )

    # 2) Missing final period
    if trimmed.endswith("Tourist comparison completed"):
        return (
            False,
            "Append a period to the end identifier. It must end exactly with 'Tourist comparison completed.' (including the period)."
        )

    # 3) Correct words but wrong case
    if trimmed.lower().endswith(END_PHRASE_LOWER):
        return (
            False,
            "Use the exact casing: 'Tourist comparison completed.' (capital 'T' and lowercase for the rest; keep the period)."
        )

    # 4) Phrase appears but not at the very end
    if END_PHRASE in trimmed:
        return (
            False,
            "Place the phrase at the absolute end of the response (after trimming trailing whitespace) with nothing after it. End exactly with: Tourist comparison completed."
        )

    # 5) Generic instruction if none of the above matched
    return (
        False,
        "End the response with the exact phrase 'Tourist comparison completed.' (case-sensitive, including the period) and do not add any characters after it."
    )

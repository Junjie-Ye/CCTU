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
 If the agent intends to invoke the `geographical_area_calculator` tool, the `urban_forest_locator` tool must be executed beforehand. Additionally, your final answer must start with the identifier "Answer:" and end with the identifier "End of Answer." Moreover, you must invoke `scientist_research_finder` and `historical_visit_locator` simultaneously in one round. In addition, you must invoke between 2 and 4 unique tool types simultaneously in at least one interaction turn during the task. Finally, your final answer must end with a period.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', 'The response must begin with the identifier "Answer:" and conclude with the identifier "End of Answer."')
- idx 4: ('Response', 'Punctuation', "Ending punctuation (Must end the agent's response with a period to ensure proper sentence closure.)")
"""

import re
from typing import Tuple

# Helper functions


def _strip_trailing_whitespace(s: str) -> str:
    """Return the string without trailing whitespace."""
    return s.rstrip()


def _first_non_whitespace_startswith(s: str, prefix: str) -> bool:
    """Check if the first non-whitespace characters start with the given prefix."""
    match = re.match(r'^\s*', s)
    start_idx = match.end() if match else 0
    return s[start_idx:].startswith(prefix)


def _endswith_token_ignoring_trailing_ws(s: str, token: str) -> bool:
    """Check if the string ends with the exact token, allowing only whitespace after it."""
    return re.search(re.escape(token) + r'\s*$', s) is not None


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that:
      - The response begins (after any leading whitespace) with the exact identifier 'Answer:'.
      - The response concludes (before any trailing whitespace) with the exact identifier 'End of Answer.'.
    """
    if not isinstance(response, str):
        return (
            False,
            "Input must be a string. Provide the full response text so the validator can check identifiers."
        )

    starts_correctly = _first_non_whitespace_startswith(response, "Answer:")
    ends_correctly = _endswith_token_ignoring_trailing_ws(
        response, "End of Answer.")

    if starts_correctly and ends_correctly:
        return (True, "Identifiers check passed: begins with 'Answer:' and ends with 'End of Answer.'.")

    if not starts_correctly and not ends_correctly:
        return (
            False,
            "The response must begin with the exact identifier 'Answer:' as the first non-whitespace token "
            "and conclude with the exact identifier 'End of Answer.' as the final non-whitespace content. "
            "Fix by: (1) Prepending 'Answer:' at the very start, e.g., 'Answer: <content> ... End of Answer.'. "
            "(2) Appending ' End of Answer.' at the very end, ensuring the period is included and no text follows it "
            "except optional whitespace."
        )
    if not starts_correctly:
        return (
            False,
            "The response must begin with the exact identifier 'Answer:' as the first non-whitespace token. "
            "Fix by placing 'Answer:' at the very start of the response, e.g., 'Answer: <content> ... End of Answer.'."
        )
    # not ends_correctly
    return (
        False,
        "The response must conclude with the exact identifier 'End of Answer.' as the final non-whitespace content. "
        "Append ' End of Answer.' to the end of the response, include the period, and ensure no characters follow it "
        "other than optional whitespace."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' (ignoring trailing whitespace).
    """
    if not isinstance(response, str):
        return (
            False,
            "Input must be a string. Provide the full response text so the validator can check punctuation."
        )

    trimmed = _strip_trailing_whitespace(response)
    if not trimmed:
        return (
            False,
            "The response is empty after trimming whitespace. Provide a non-empty response that ends with a period '.'."
        )

    if trimmed[-1] == '.':
        return (True, "Punctuation check passed: the response ends with a period '.'.")
    else:
        return (
            False,
            "The response must end with a period '.' as the final character (ignoring trailing whitespace). "
            "Add a terminating period to the end, for example: '... End of Answer.'. "
            "Do not include any characters after the final period other than optional whitespace."
        )

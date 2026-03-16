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
 The total number of tool calls must be in the range of 2 to 3. The response must end with a period. Additionally, the response must include the keyword "Difference:" immediately before stating the final numerical answer to explicitly delimit the result.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The response must end with a period.')
- idx 2: ('Response', 'Identifiers', 'The response must include the keyword "Difference:" immediately before stating the final numerical answer to explicitly delimit the result.')
"""

import re
from typing import Tuple, List, Match

# Shared regular expressions
NUMBER_RE = re.compile(
    r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?')
DIFFERENCE_WITH_NUMBER_RE = re.compile(
    r'Difference:\s*([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?)'
)
DIFFERENCE_LITERAL_RE = re.compile(r'Difference:')


def _find_all_numbers(response: str) -> List[Match[str]]:
    """
    Return a list of regex Match objects for all numeric tokens in the response.
    Supports integers, decimals, thousand separators, and scientific notation.
    """
    return list(NUMBER_RE.finditer(response))


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    - The final visible character should be a period '.' (no extra trailing whitespace).
    """
    if response is None:
        return (
            False,
            "Response is missing. Provide a non-empty final answer that ends with a period '.' as the last character."
        )

    trimmed = response.rstrip()
    if not trimmed:
        return (
            False,
            "Response is empty. Provide content and ensure the very last character is a period '.'."
        )

    if not trimmed.endswith("."):
        return (
            False,
            "The final response must end with a period '.' as the last character. "
            "Adjust your output so the last character is '.' (e.g., 'Difference: 42.')."
        )

    return (
        True,
        "Punctuation check passed: the response ends with a period."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response includes the exact keyword 'Difference:'.
    - 'Difference:' appears exactly once.
    - A numeric value appears immediately after 'Difference:' (optionally separated by whitespace).
    - The numeric value following 'Difference:' is the final numeric token in the entire response
      (i.e., no other numbers appear after it).
    """
    if response is None or not response:
        return (
            False,
            "Response is empty. Include the exact keyword 'Difference:' followed immediately by the final numeric answer "
            "(e.g., 'Difference: 12.5')."
        )

    # Check presence and uniqueness of 'Difference:'
    diff_occurrences = list(DIFFERENCE_LITERAL_RE.finditer(response))
    if len(diff_occurrences) == 0:
        return (
            False,
            "Missing required keyword. Include the exact keyword 'Difference:' followed immediately by the final numeric answer "
            "with no intervening words (e.g., 'Difference: 27')."
        )
    if len(diff_occurrences) > 1:
        return (
            False,
            "The keyword 'Difference:' must appear exactly once. Remove duplicates and keep a single 'Difference:' "
            "before the final numeric answer (e.g., 'Difference: 27')."
        )

    # Ensure a number appears immediately after 'Difference:'
    m = DIFFERENCE_WITH_NUMBER_RE.search(response)
    if not m:
        return (
            False,
            "After 'Difference:' you must place a numeric value immediately (spaces allowed), with no other words in between. "
            "Example: 'Difference: 42' or 'Difference: -3.14e2'."
        )

    # Ensure that the number after 'Difference:' is the final numeric token in the response
    all_numbers = _find_all_numbers(response)
    if not all_numbers:
        return (
            False,
            "A numeric value must follow 'Difference:'. Provide a valid number after the keyword "
            "(e.g., 'Difference: 10')."
        )

    diff_num_span = m.span(1)
    last_num_span = all_numbers[-1].span()

    if diff_num_span != last_num_span:
        return (
            False,
            "The numeric value following 'Difference:' must be the final numeric token in the entire response. "
            "Move all other numbers before 'Difference:' or remove trailing numbers. "
            "Example of a valid ending: '... Additional details. Difference: 123.'"
        )

    return (
        True,
        "Identifier check passed: 'Difference:' appears once and is immediately followed by the final numeric answer."
    )

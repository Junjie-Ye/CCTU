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
 The answer must end with a period (.) to ensure proper sentence closure. If the agent chooses to use these tools, philosopher_concept_identifier must precede historical_figure_info. Philosopher_concept_identifier tool must be invoked at most once during the process.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', '(Response, Punctuation, "Ending punctuation (.) with concrete example: \'The answer must end with a period (.)")')
"""

from typing import Tuple


def _trim_trailing_whitespace(text: str) -> str:
    """
    Helper to remove trailing whitespace characters while preserving the rest of the content.
    """
    return text.rstrip()


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period (.) as the last non-whitespace character.
    Additional safeguards:
    - Reject empty or whitespace-only responses.
    - Reject ellipses ('..' or '...') as the ending; require exactly one final period.
    - Reject any trailing characters after the final period (e.g., quotes, parentheses).
    Returns:
        (bool, str): A tuple where bool indicates compliance, and str provides actionable guidance.
    """
    if response is None:
        return (
            False,
            "Response is None. Provide a non-empty final answer that ends with a single period '.' as the last character."
        )

    trimmed = _trim_trailing_whitespace(response)

    if len(trimmed) == 0:
        return (
            False,
            "Response is empty or whitespace only. Provide a non-empty final answer that ends with a single period '.' as the last character."
        )

    # Disallow ellipsis endings ('..' or '...') – must be exactly one final period
    if trimmed.endswith("...") or trimmed.endswith(".."):
        return (
            False,
            "Do not end with an ellipsis ('..' or '...'). End the response with exactly one period '.' as the final character, with no extra characters after it."
        )

    # Check last character is a period
    last_char = trimmed[-1]
    if last_char != ".":
        return (
            False,
            "The final non-whitespace character must be a period '.'. Edit the response so that it ends with a single '.' and no characters after it."
        )

    # Ensure the period is truly the final character (no trailing quotes, brackets, etc.)
    # Since last_char is '.', this is satisfied; however, guard against cases like '. '' or '.\n' by prior rstrip.
    # Also ensure there are no trailing characters after a period if user includes formatting anomalies.
    # Already enforced by rstrip + last_char check.

    return (
        True,
        "OK: The response ends with exactly one period '.' as the final non-whitespace character."
    )

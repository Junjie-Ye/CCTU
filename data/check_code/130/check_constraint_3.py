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
 The solution must be completed in a number of interaction rounds between 2 and 3 (inclusive), while making at least 2 separate tool calls to retrieve the required specifications. Additionally, the 'product_and_appliance_specification_retriever' tool must not be invoked more than 2 times in total throughout the task. Your final response must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 3: ('Response', 'Punctuation', "(Main Category, Response, Ending punctuation (The agent's response must end with a period to ensure proper sentence closure.))")
"""

from typing import Tuple


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period.
    The check is performed on the last non-whitespace character.
    Accepts ASCII '.' or the full-width Chinese '。' as a terminal period.

    Parameters:
        response (str): The agent's final response.

    Returns:
        Tuple[bool, str]: 
            - bool: True if the constraint is satisfied; False otherwise.
            - str: An English explanation with actionable guidance to fix issues.
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string. Ensure the final output is a string whose last non-whitespace character is a period '.'."
        )

    stripped = response.rstrip()
    if not stripped:
        return (
            False,
            "Response is empty after trimming whitespace. Provide a non-empty final answer that ends with a period '.'."
        )

    last_char = stripped[-1]
    if last_char in {'.', '。'}:
        return (
            True,
            "Punctuation constraint satisfied: the final non-whitespace character is a period."
        )

    return (
        False,
        f"The final non-whitespace character is '{last_char}', not a period. Trim trailing whitespace and make the last character a period '.' (e.g., append '.' at the end of the response)."
    )

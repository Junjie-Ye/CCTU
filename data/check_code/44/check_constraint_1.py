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
 You must use the provided tools to find the answer. The agent must not call tools more than twice. The final response must end with a period and must not include any exclamation marks.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The response must end with a period.')
"""

from typing import Tuple


def _last_non_whitespace_char(s: str) -> str:
    """
    Return the last non-whitespace character of the string, or '' if none exists.
    """
    stripped = s.rstrip()
    return stripped[-1] if stripped else ''


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate the punctuation constraint:
    - The response must end with a period '.' (ignoring trailing whitespace).

    Returns:
        (bool, str): 
            - bool indicates whether the response satisfies the constraint.
            - str provides detailed, actionable guidance in English.
    """
    if response is None:
        return (
            False,
            "The response is None. Provide a non-empty string that ends with a period '.'."
        )
    last_char = _last_non_whitespace_char(response)
    if last_char == '':
        return (
            False,
            "The response is empty or only whitespace. Provide a substantive answer and ensure it ends with a single period '.' with no characters after it except optional whitespace."
        )
    if last_char != '.':
        return (
            False,
            "The response must end with a period '.'. Modify the output so that the last non-whitespace character is a period. Example: '...final sentence.'."
        )
    return (
        True,
        "Punctuation check passed: the response ends with a period '.' as required."
    )

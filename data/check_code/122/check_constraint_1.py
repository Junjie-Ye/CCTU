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
 The answer must be at least 50 characters in length to ensure a detailed explanation of the calculation process, and it must end with a question mark (?).

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The response must end with a question mark (?).')
"""

from typing import Tuple


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with an ASCII question mark (?).

    Rules enforced:
    - The last non-whitespace character in the entire response must be '?' (ASCII 0x3F).

    Returns:
        (bool, str): 
            - bool: True if valid, otherwise False.
            - str: Detailed English guidance to fix the violation (or confirmation if valid).
    """
    if response is None:
        return (
            False,
            "The response is None. Provide a non-empty string that ends with an ASCII question mark '?'."
        )

    trimmed = response.rstrip()
    if not trimmed:
        return (
            False,
            "The response is empty after trimming trailing whitespace. Ensure the final character is an ASCII question mark '?'."
        )

    last_char = trimmed[-1]

    if last_char == '?':
        return (
            True,
            "Valid: The response ends with an ASCII question mark '?' after trimming trailing whitespace."
        )

    if last_char == '?':
        return (
            False,
            "Invalid ending punctuation: The response ends with a full-width question mark '?'. Replace it with the ASCII '?' so the final character is exactly '?'."
        )

    # Provide helpful context about what the last char actually is
    visible_last = repr(last_char)
    return (
        False,
        f"Invalid ending punctuation: The last non-whitespace character is {visible_last}. "
        "The response must end with a single ASCII question mark '?'. "
        "Action: Edit the final sentence so that '?' is the last character of the entire response "
        "(e.g., move any trailing notes, citations, or signatures before the question mark, "
        "and remove any characters after '?')."
    )

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
 The answer must be presented as a complete sentence ending with a period. You must use between 2 to 4 total tool calls and complete the task within 2 to 3 interaction turns. The final response must be between 10 and 20 words in length. Additionally, you may call the 'marine_biology_facts' tool no more than 2 times during your solution process. If the agent intends to use both the 'marine_biology_facts' and 'factual_information_retriever' tools, their execution must be coordinated in a single action.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The final answer must end with a period to ensure proper sentence closure.')
"""

import re
from typing import Tuple


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with exactly one period '.' as the last non-whitespace character.

    Args:
        response: The model's final answer as a string.

    Returns:
        (is_valid, message): 
            - is_valid: True if the response ends with exactly one period, False otherwise.
            - message: Detailed English guidance to correct the output if invalid.
    """
    if response is None:
        return (
            False,
            "Response is missing. Provide a single complete sentence whose last character is a period '.'."
        )

    trimmed = response.rstrip()
    if not trimmed:
        return (
            False,
            "Response is empty after trimming. Provide one sentence ending with a period '.' as the final character."
        )

    # Reject ellipses or multiple trailing periods such as '..' or '...'
    if re.search(r'\.\.+$', trimmed):
        return (
            False,
            "Do not end with multiple periods or ellipses. End with exactly one period '.' as the final character."
        )

    # If there is a period followed only by closing quotes/brackets at the very end, it's invalid: '.' must be last.
    if re.search(r'\.(?=[\'")\]]+$)', trimmed):
        return (
            False,
            "The last character must be a period '.'. Do not place closing quotes or brackets after the final period."
        )

    # Validate the last non-whitespace character is exactly '.'
    if trimmed.endswith('.'):
        return (
            True,
            "Validation passed: the final answer ends with exactly one period as the last character."
        )

    last_char = trimmed[-1]
    return (
        False,
        f"The final answer must end with a period '.'. It currently ends with '{last_char}'. "
        "Replace the final character with a single period and avoid using '?', '!', or quotes after it."
    )

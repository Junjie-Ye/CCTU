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
 The total number of tool calls the agent must execute must be between 3 and 5, inclusive. Additionally, the final response must be between 50 and 100 words in length. The response must end with a period to ensure proper sentence closure. Furthermore, each unique tool may be called at most once during the task execution. Usage of `bridge_identifier` is conditional upon the prior execution of `event_locator`, and subsequently, `infrastructure_info_retriever` relies on the successful completion of `bridge_identifier`.

response_constraints_non_length:
- idx 2: ('Response', 'Punctuation', '(Response, Ending punctuation, The response must end with a period to ensure proper sentence closure.)')
"""

from typing import Tuple


def _last_visible_char(text: str) -> str:
    """
    Return the last non-whitespace character of the given text.
    If none exists, return an empty string.
    """
    if not isinstance(text, str):
        return ""
    for ch in reversed(text):
        if not ch.isspace():
            return ch
    return ""


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' after trimming whitespace.

    Returns:
        (bool, str): 
            - bool indicates whether the response satisfies the punctuation constraint.
            - str provides actionable English guidance to fix issues when invalid.
    """
    last_char = _last_visible_char(response or "")
    if not last_char:
        return (
            False,
            "The response is empty or whitespace only. Provide a non-empty final answer and ensure the very last character (after trimming whitespace) is a period '.'. Example: 'All required findings are summarized here.'"
        )
    if last_char != ".":
        return (
            False,
            "The response must end with a period '.' as the final character. Replace the current ending punctuation "
            f"(it currently ends with '{last_char}') or append a period so that the last character is '.'. Avoid ending with '!', '?', ';', ':', or an ellipsis. Example: 'The analysis supports this conclusion.'"
        )
    return (
        True,
        "Valid: The response ends with a period '.' as required. Keep the period as the final character after any quotes or parentheses."
    )

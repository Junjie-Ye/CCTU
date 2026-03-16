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
 The answer must be concise and must not exceed 150 words. Additionally, if the agent chooses to invoke a biographical_info_retriever, then an invention_info_retriever must be invoked simultaneously in the same action instruction. At least 2 unique tool types must be invoked simultaneously in one interaction turn during the task. The answer must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 2: ('Response', 'Punctuation', 'The answer must end with a period to ensure proper sentence closure.')
"""

from typing import Tuple


def _rtrim(text: str) -> str:
    """
    Helper: return the string with trailing whitespace removed.
    """
    return text.rstrip()


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period '.' as the last character.
    Rules:
      - After trimming trailing whitespace, the very last character must be '.'.
      - Do not leave any trailing quotes, brackets, emojis, or other punctuation after the period.
    Returns:
      (True, message) if valid
      (False, detailed guidance) if invalid
    """
    trimmed = _rtrim(response or "")
    if not trimmed:
        return (
            False,
            "The response is empty. Provide a concise final answer and ensure the last character is a period '.'."
        )

    if trimmed.endswith("."):
        return (
            True,
            "OK: The response ends with a period '.' as required."
        )

    last_char = trimmed[-1]
    return (
        False,
        (
            "The response must end with a period '.' as the final character. "
            f"Current last character is '{last_char}'. "
            "Fix by making '.' the very last character after trimming whitespace, e.g., '...answer.'. "
            "Avoid ending with quotes, brackets, emojis, or other punctuation after the period (e.g., not 'answer.\"' or 'answer.)')."
        )
    )

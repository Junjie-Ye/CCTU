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
 Your response must include the identifier "[Answer]" immediately before the final answer to clearly separate the answer from any preceding content. Additionally, you must ensure that the total number of tool calls made does not exceed 3 and that the total number of interaction rounds falls within a range of 2 to 5 (inclusive).

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(The response must include the identifier "[Answer]" immediately before the final answer to clearly separate the answer from any preceding content.)')
"""

import re
from typing import Tuple, Optional


def _get_section_after_header(text: str, header: str) -> Optional[str]:
    """
    Return the substring that appears after the first occurrence of `header`.
    If the header is not found, return None.
    """
    m = re.search(re.escape(header), text)
    if not m:
        return None
    return text[m.end():]


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the identifier "[Answer]" immediately before
    the final answer content.

    Rules enforced:
    - If a [FINAL ANSWER] section exists, the first non-whitespace token after the
      [FINAL ANSWER] header must be "[Answer]".
    - If no [FINAL ANSWER] section exists, the entire message (after trimming leading
      whitespace) must start with "[Answer]".
    - The identifier is case-sensitive and must include brackets exactly as "[Answer]".
    """
    if not isinstance(response, str):
        return (
            False,
            "Invalid input: response must be a string. Provide a string where the final answer "
            "is explicitly prefixed by the exact token '[Answer]'."
        )

    # Case 1: Explicit [FINAL ANSWER] section present
    after_final = _get_section_after_header(response, "[FINAL ANSWER]")
    if after_final is not None:
        tail = after_final.lstrip()
        if tail.startswith("[Answer]"):
            return (
                True,
                "Valid: The [FINAL ANSWER] section begins with the required identifier '[Answer]'."
            )
        # If [Answer] exists but not at the beginning of the final-answer section
        if "[Answer]" in tail:
            return (
                False,
                "Place the identifier '[Answer]' as the very first non-whitespace token in the "
                "[FINAL ANSWER] section. Do not include any text, punctuation, or other tags "
                "before it. Example:\n[FINAL ANSWER]\n[Answer] <your final answer here>"
            )
        # [Answer] not found at all within the final-answer section
        return (
            False,
            "Insert the exact, case-sensitive identifier '[Answer]' as the first non-whitespace "
            "token in the [FINAL ANSWER] section. Example:\n[FINAL ANSWER]\n[Answer] <your final answer here>"
        )

    # Case 2: No [FINAL ANSWER] header — require the message to start with [Answer]
    trimmed = response.lstrip()
    if trimmed.startswith("[Answer]"):
        return (
            True,
            "Valid: The response starts with the required identifier '[Answer]'."
        )

    if "[Answer]" in response:
        return (
            False,
            "Move the identifier '[Answer]' to the very start of the final answer content. The first "
            "non-whitespace characters in your final answer must be '[Answer]'. Preferably format as:\n"
            "[FINAL ANSWER]\n[Answer] <your final answer here>\nIf you choose not to include [FINAL ANSWER], "
            "ensure the entire message begins with '[Answer]'."
        )

    return (
        False,
        "Prepend the exact, case-sensitive identifier '[Answer]' to the final answer. It must be the first "
        "non-whitespace token. Recommended format:\n[FINAL ANSWER]\n[Answer] <your final answer here>"
    )

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
 The answer must conclude with "Vietnam." to ensure a clear and consistent ending for the location answer. You are allowed a maximum of two interaction turns to solve this question, and you may use the `historical_event_locator` tool at most once during the solution process.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Response, End identifier, The agent\'s response must conclude with the phrase "Vietnam." to ensure a clear and consistent ending for the location answer.)')
"""

from typing import Tuple
import re

REQUIRED_ENDING = "Vietnam."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the agent's response concludes with the exact phrase 'Vietnam.'
    (capital V, lowercase remainder, followed by a single period) as the final
    non-whitespace characters, with nothing after it.

    Returns:
        (bool, str): A tuple where the bool indicates pass/fail, and the str
        provides detailed, English guidance to correct the output if it fails.
    """
    if not isinstance(response, str):
        return (
            False,
            "Fail: The response is not a string. Ensure the output is a single string that ends exactly with 'Vietnam.'."
        )

    trimmed = response.rstrip()

    # Pass condition: after trimming trailing whitespace, it must end exactly with 'Vietnam.'
    if trimmed.endswith(REQUIRED_ENDING):
        return (
            True,
            "Pass: The response correctly concludes with the exact phrase 'Vietnam.' as the final non-whitespace characters."
        )

    # Common failure: missing period
    if trimmed.endswith("Vietnam"):
        return (
            False,
            "Fail: The response ends with 'Vietnam' but is missing the required period. "
            "Fix: Append a period so the final non-whitespace characters are exactly 'Vietnam.'."
        )

    # Common failure: incorrect capitalization (e.g., 'vietnam.' or 'VIETNAM.')
    if trimmed.lower().endswith("vietnam.") and not trimmed.endswith(REQUIRED_ENDING):
        return (
            False,
            "Fail: The response ends with 'vietnam.' but has incorrect capitalization. "
            "Fix: Use exact casing and punctuation — the final non-whitespace characters must be 'Vietnam.'."
        )

    # The phrase appears but is not the final content (extra characters after it)
    idx = trimmed.rfind(REQUIRED_ENDING)
    if idx != -1 and idx + len(REQUIRED_ENDING) != len(trimmed):
        trailing = trimmed[idx + len(REQUIRED_ENDING):]
        trailing_preview = trailing[:40].replace("\n", "\\n")
        return (
            False,
            f"Fail: The phrase 'Vietnam.' appears but is not the final content; extra characters follow: '{trailing_preview}'. "
            "Fix: Remove everything after 'Vietnam.' so it is the very last non-whitespace content."
        )

    # Generic failure guidance
    return (
        False,
        "Fail: The response must conclude with the exact phrase 'Vietnam.' (capital V, trailing period) as the final non-whitespace characters. "
        "Fix: Ensure the trimmed output ends exactly with 'Vietnam.' and that no characters (quotes, emojis, tags, or extra sentences) follow it."
    )

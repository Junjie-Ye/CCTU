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
 The response must be at most 200 words to ensure conciseness while maintaining sufficient detail, must begin with the phrase "The annual production in tons is: " to ensure a consistent and recognizable opening, the agent must execute a total number of tool calls within the range of 5 to 7 to balance efficiency and thoroughness in information gathering, and must complete the task within a total of 5 to 8 interaction turns to balance efficiency and thoroughness in the solution process.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Response, Start identifier, "Start identifier (Mandates that the agent\'s response must begin with the phrase \'The annual production in tons is: \' to ensure a consistent and recognizable opening.)")')
"""

from typing import Tuple

REQUIRED_START_IDENTIFIER = "The annual production in tons is: "


def _preview_start(text: str, n: int = 60) -> str:
    """
    Returns a cleaned preview of the first n characters for diagnostics.
    """
    snippet = text[:n].replace("\n", "\\n").replace("\r", "\\r")
    return snippet


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response begins exactly with the required start identifier:
    'The annual production in tons is: ' (including the trailing space).

    Returns:
        (bool, str): A tuple where bool indicates pass/fail and str provides
        detailed, actionable guidance in English.
    """
    required = REQUIRED_START_IDENTIFIER

    # Exact compliance
    if response.startswith(required):
        return True, "Pass: Response starts with the exact required start identifier."

    # Missing trailing space after colon
    no_space_variant = "The annual production in tons is:"
    if response.startswith(no_space_variant) and not response.startswith(required):
        return (
            False,
            "Fail: The start identifier is missing a single space after the colon. "
            "Begin exactly with: 'The annual production in tons is: ' (note the space), "
            "then continue your content. Example: "
            "'The annual production in tons is: 123,456 based on tool observations.'"
        )

    # Case-insensitive match indicates casing error
    if response.lower().startswith(required.lower()):
        return (
            False,
            "Fail: The start identifier is case-sensitive. Use exactly: "
            "'The annual production in tons is: ' (same casing and spacing). "
            f"Current start preview: '{_preview_start(response)}'"
        )

    # Leading content before the identifier (e.g., whitespace, headers, or text)
    if response.lstrip().startswith(required) and not response.startswith(required):
        return (
            False,
            "Fail: No text or whitespace may precede the start identifier. "
            "Remove any leading spaces, newlines, or headings. The very first characters "
            "must be: 'The annual production in tons is: '"
        )

    # Generic failure with diagnostic preview
    return (
        False,
        "Fail: The response must begin exactly with the phrase 'The annual production in tons is: ' "
        "(including the trailing space). Do not include any preamble, headings, or emojis before it, "
        "and match the case and punctuation precisely. "
        f"Current start preview: '{_preview_start(response)}'. "
        "Fix by making this the first characters of your output."
    )

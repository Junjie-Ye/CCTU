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
 If the agent intends to invoke the average_altitude_calculator tool, the historical_event_locator tool must be executed beforehand. Each tool must be called at most once. The final answer must be between 10 and 50 words in length, and the agent's response must begin with the identifier "Answer Start: " to indicate the start of the final answer.

response_constraints_non_length:
- idx 3: ('Response', 'Identifiers', 'The agent\'s response must begin with the identifier "Answer Start: " to indicate the beginning of the final answer.')
"""

from typing import Tuple

# Constants for identifier validation
REQUIRED_PREFIX = "Answer Start: "


def _lstrip_bom_and_space(s: str) -> str:
    """
    Remove optional BOM and leading whitespace so we can test the true start.
    """
    if s is None:
        return ""
    # Strip UTF-8 BOM if present, then leading whitespace/newlines
    s = s.lstrip("\ufeff")
    return s.lstrip()


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the agent's response begins with the exact identifier:
    'Answer Start: ' (including the trailing space), with no preceding text.

    Returns:
        (bool, str): 
            - bool indicates pass/fail.
            - str provides a detailed, actionable English message.
    """
    # Normalize the start for reliable checking
    normalized = _lstrip_bom_and_space(
        response if isinstance(response, str) else "")

    # Exact, case-sensitive, space-sensitive check
    if normalized.startswith(REQUIRED_PREFIX):
        return True, "Valid: The response begins with the exact required identifier 'Answer Start: '."

    # Provide targeted diagnostics
    lower_prefix = REQUIRED_PREFIX.lower()
    if normalized.lower().startswith(lower_prefix) and not normalized.startswith(REQUIRED_PREFIX):
        return (
            False,
            "Invalid: The identifier casing or spacing is incorrect. Use exact text and spacing: 'Answer Start: ' "
            "with uppercase A and S, a colon, and a single trailing space. Do not alter case or omit the space."
        )

    if normalized.startswith("Answer Start:") and not normalized.startswith(REQUIRED_PREFIX):
        return (
            False,
            "Invalid: The space after the colon is missing. Start exactly with 'Answer Start: ' (note the trailing space), "
            "then continue with your  final answer text."
        )

    if normalized.startswith("Answer Start") and not normalized.startswith("Answer Start:"):
        return (
            False,
            "Invalid: The colon after 'Answer Start' is missing. Start exactly with 'Answer Start: ' "
            "(including the colon and a trailing space)."
        )

    if "Answer Start: " in normalized and not normalized.startswith(REQUIRED_PREFIX):
        return (
            False,
            "Invalid: The required identifier 'Answer Start: ' appears, but not at the very beginning. "
            "Do not include any text, tags, or newlines before it. The response must start with 'Answer Start: '."
        )

    # Generic guidance
    preview = normalized[:40].replace("\n", "\\n")
    return (
        False,
        f"Invalid: The response does not start with the required identifier 'Answer Start: '. "
        f"Begin the response exactly with 'Answer Start: ' followed by the final answer text. "
        f"Do not add any content before it. Current start: '{preview}'"
    )

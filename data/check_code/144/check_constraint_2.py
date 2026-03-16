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
 The agent must invoke the `merged_event_data_retriever` function twice in a single round. The final response must be between 50 and 200 characters in length to ensure clarity and conciseness, and must begin with the phrase "Casualty difference: " to ensure a clear and recognizable format for the final answer. Additionally, the total number of interaction turns the agent must take to complete the task must fall within the range of 1 to 2, inclusive, to ensure efficiency and prevent infinite loops.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', 'The response must begin with the phrase "Casualty difference: " to ensure a clear and recognizable format for the final answer.')
"""

from typing import Tuple

REQUIRED_PREFIX = "Casualty difference: "


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response begins exactly with the required identifier phrase:
    'Casualty difference: ' (note the exact casing, colon, and a single space after the colon).
    Returns:
      - (True, detailed success message) if compliant.
      - (False, detailed correction instructions) if not compliant.
    """
    if response.startswith(REQUIRED_PREFIX):
        return True, "Pass: Response starts with the exact required phrase 'Casualty difference: '."

    # Specific diagnostics to provide actionable feedback
    if not response:
        return False, (
            "Fail: The response is empty. Start the response exactly with 'Casualty difference: ' "
            "followed by your single-sentence content."
        )

    if response.startswith("Casualty difference:") and not response.startswith(REQUIRED_PREFIX):
        return False, (
            "Fail: Missing a single space after the colon. Start exactly with 'Casualty difference: ' "
            "(note the space after ':')."
        )

    if response.lstrip().startswith(REQUIRED_PREFIX) and not response.startswith(REQUIRED_PREFIX):
        leading = len(response) - len(response.lstrip())
        return False, (
            f"Fail: Found {leading} leading whitespace character(s) before the required phrase. "
            "Remove all leading characters so the response begins at position 0 with "
            "'Casualty difference: '."
        )

    if response[:len(REQUIRED_PREFIX)].lower() == REQUIRED_PREFIX.lower() and not response.startswith(REQUIRED_PREFIX):
        return False, (
            "Fail: The prefix has incorrect casing or punctuation. Use exact case and spacing: "
            "'Casualty difference: ' (capital C and D, a colon, then a single space)."
        )

    if "Casualty difference:" in response and not response.startswith("Casualty difference:"):
        return False, (
            "Fail: The required phrase appears later in the text. Move it to the very beginning and ensure a single "
            "space follows the colon: 'Casualty difference: '."
        )

    return False, (
        "Fail: The response must begin exactly with 'Casualty difference: ' (case-sensitive, includes the colon and a "
        "single space after it). Place this phrase at index 0, then continue the sentence."
    )

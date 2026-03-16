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
 The response must start with the phrase "The main crop is", must be between 50 and 100 words in length, the total number of interaction turns must fall within a range of 3 to 6 (inclusive), the agent can make at most 5 tool calls in total to answer the question. If the agent invokes the agricultural_data_analyzer tool, it must first call the earthquake_event_locator tool.The earthquake_event_locator can be called at most 1 time, and the agricultural_data_analyzer can be called at most 1 time.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'The response must start with the phrase "The main crop is".')
- idx 3: ('Response', 'Punctuation', '(Response, Punctuation, The response must end with a period.)')
"""

from typing import Tuple

# Helper functions


def _first_non_whitespace_prefix(response: str) -> str:
    """Return the response with only leading whitespace removed (for start-phrase checks)."""
    return response.lstrip() if response is not None else ""


def _last_non_whitespace_char(response: str) -> str:
    """Return the last non-whitespace character of the response, or empty string if none."""
    if response is None:
        return ""
    stripped = response.rstrip()
    return stripped[-1] if stripped else ""


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Constraint: The response must start with the phrase "The main crop is".
    - The check is case-sensitive.
    - No characters (including whitespace) may appear before the phrase.
    """
    required_phrase = "The main crop is"
    head = _first_non_whitespace_prefix(response)

    if not head.startswith(required_phrase):
        return (
            False,
            (
                "Your response must start exactly with the phrase 'The main crop is' "
                "(case-sensitive) at the very beginning. Do not add any characters, "
                "numbers, emojis, or whitespace before it. Example of a valid start: "
                "'The main crop is maize in the affected region...' Adjust your output "
                "so the first non-whitespace characters are precisely: The main crop is"
            ),
        )
    return (
        True,
        "Pass: The response begins with the exact required phrase 'The main crop is'."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Constraint: The response must end with a period.
    - The final non-whitespace character must be a '.'.
    """
    last_char = _last_non_whitespace_char(response)

    if last_char != ".":
        return (
            False,
            (
                "Your response must end with a period. Ensure the very last non-whitespace "
                "character is '.' and avoid trailing quotes, emojis, or other punctuation "
                "after the final period. Example ending: '...food security.'"
            ),
        )
    return (
        True,
        "Pass: The response ends with a period as required."
    )

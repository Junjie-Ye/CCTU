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
 The agent must invoke between 1 and 2 unique tools simultaneously in at least one interaction turn during the solution process, while ensuring that no turn exceeds 2 simultaneous tool invocations. The agent is allowed a maximum of 10 total tool calls in the solution process. If the agent intends to invoke `artwork_artist_locator`, `desert_museum_locator` must be executed beforehand. If the agent intends to invoke `biographical_info_retriever`, `artwork_artist_locator` must be executed beforehand. If the agent intends to invoke `population_data_retriever`, `biographical_info_retriever` must be executed beforehand. If the agent intends to invoke `explorer_achievement_finder`, `population_data_retriever` must be executed beforehand. If the agent intends to invoke `age_calculator`, `explorer_achievement_finder` must be executed beforehand. If the agent intends to invoke `advanced_calculator`, `age_calculator` must be executed beforehand. The final response must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', '(Main Category, Response, Subcategory, Punctuation, "Ending punctuation (Period must be used at the end of the agent\'s response to ensure proper sentence closure.)")')
"""

from typing import Tuple

# Helper set of characters that may legally trail the final period (e.g., closing quotes/brackets)
_TRAILING_CLOSERS = set(')]}>\'"»”’›')


def _last_meaningful_char(text: str) -> str:
    """
    Return the last meaningful character of the response, ignoring:
    - trailing whitespace
    - trailing closing quotes/brackets/angle quotes commonly used in prose

    If no meaningful character exists, return an empty string.
    """
    if text is None:
        return ''
    s = text.rstrip()
    # Strip trailing closers (e.g., ... .")  -> last meaningful should be '.'
    while s and s[-1] in _TRAILING_CLOSERS:
        s = s[:-1].rstrip()
    return s[-1] if s else ''


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period for proper sentence closure.
    The check ignores trailing whitespace and allows closing quotes/brackets after the period.

    Pass criteria:
    - The last meaningful character (after trimming whitespace and trailing closers) is '.'.

    Returns:
        (bool, str): (is_valid, detailed_feedback_in_english)
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. Provide a non-empty final answer and ensure the last meaningful character is a period '.'. Example: Final result here."
        )

    last_char = _last_meaningful_char(response)

    if last_char == '.':
        return (
            True,
            "Valid: The final meaningful character (ignoring trailing quotes/brackets) is a period."
        )

    # Provide targeted guidance based on the detected last character
    if last_char in {'!', '?'}:
        return (
            False,
            "The response ends with an exclamation or question mark. Replace the final punctuation with a period. If the answer ends with a closing quote or parenthesis, put the period before it. Examples: Correct -> Hello.  \"Hello.\"  (Hello.)."
        )
    if last_char in {',', ';', ':'}:
        return (
            False,
            "The response ends with a comma, semicolon, or colon. Use a period to close the final sentence. If there is a trailing quote or parenthesis, place the period before it. Example: Summary of findings."
        )
    if last_char == '':
        return (
            False,
            "No meaningful ending character found. Ensure the final answer ends with a period '.', optionally followed by a closing quote or parenthesis. Example: Final conclusion."
        )

    # Default guidance for any other non-period ending (letters, digits, other symbols)
    return (
        False,
        "The response does not end with a period. Ensure the last meaningful character is '.'. If the answer ends with a closing quote or parenthesis, place the period before it. Examples: Correct -> Result statement.  \"Result statement.\"  (Result statement.)."
    )

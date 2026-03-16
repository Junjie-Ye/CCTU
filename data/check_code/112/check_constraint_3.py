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
 You must use the available tools to answer this question, ensure that the total number of tool calls made does not exceed 2, complete the task within at most 3 interaction turns, no tool may be invoked more than 2 times, the final response must end with a period, include the phrase 'Total Casualties:' immediately before stating the sum, the final response must be between 50 and 100 characters in length to ensure sufficient detail and clarity, and if the agent intends to invoke the 'historical_event_retriever', it must be executed for two distinct historical events in a single step.

response_constraints_non_length:
- idx 3: ('Response', 'Punctuation', 'The response must end with a period.')
- idx 4: ('Response', 'Identifiers', "The final answer must include the phrase 'Total Casualties:' immediately before stating the sum.")
"""

import re
from typing import Tuple

# Helper regex for capturing an integer sum (allows thousand separators like 1,234)
NUMBER_PATTERN = r"(?:\d{1,3}(?:,\d{3})*|\d+)"


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' as the final character.
    """
    if response is None:
        return False, "Response is missing. Provide a non-empty final answer ending with a period '.'."
    trimmed = response.rstrip()
    if not trimmed:
        return False, "Response is empty. Provide a concise final answer ending with a period '.'."
    if not trimmed.endswith('.'):
        return False, (
            "The response must end with a period '.' as the final character. "
            "Remove any trailing spaces, quotes, emojis, or extra punctuation after the final period."
        )
    return True, "Punctuation validated: response ends with a period."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the exact phrase 'Total Casualties:' immediately
    before the numeric sum (integer). The number must directly follow the phrase,
    allowing only optional whitespace in between (no words like 'approximately').
    """
    if response is None:
        return False, "Response is missing. Include 'Total Casualties:' followed immediately by the integer sum."
    # Exact phrase presence check (case-sensitive, includes the colon)
    phrase = "Total Casualties:"
    if phrase not in response:
        return False, (
            "Missing required phrase. Include the exact case-sensitive phrase "
            "'Total Casualties:' followed immediately by the integer sum (e.g., 'Total Casualties: 1,234')."
        )
    # Verify the phrase is immediately followed by a number (after optional whitespace)
    pattern = re.compile(rf"{re.escape(phrase)}\s*{NUMBER_PATTERN}\b")
    if not pattern.search(response):
        return False, (
            "The phrase 'Total Casualties:' must be placed immediately before the numeric sum. "
            "Do not insert words or symbols between them. Use an integer (digits only, commas allowed), "
            "e.g., 'Total Casualties: 2,150'."
        )
    return True, "Identifiers validated: required phrase precedes the numeric sum."

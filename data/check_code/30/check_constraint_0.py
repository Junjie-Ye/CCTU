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
 The response must end with a period and must include the identifier "km/h". Additionally, the agent must call the historical_weather_data_retriever tool at most once.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', "Mandates that the agent's response must end with a period to ensure proper sentence closure.")
- idx 1: ('Response', 'Identifiers', '(Mandates that the agent\'s response must include the identifier "km/h" to align with the question\'s unit and provide a recognizable ending.)')
"""

from typing import Tuple

REQUIRED_IDENTIFIER = "km/h"


def _last_non_whitespace_char(s: str):
    """
    Return a tuple of (char, index) for the last non-whitespace character in s.
    If no such character exists, returns (None, -1).
    """
    i = len(s) - 1
    while i >= 0 and s[i].isspace():
        i -= 1
    if i < 0:
        return None, -1
    return s[i], i


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the response ends with a period.
    Requirement: The last visible (non-whitespace) character must be '.'.
    """
    if not isinstance(response, str):
        return False, "The response must be a string. Provide a textual response ending with a period."

    last_char, idx = _last_non_whitespace_char(response)
    if last_char == '.':
        return True, "Pass: The response ends with a period as required."
    if last_char is None:
        return False, "The response is empty or only whitespace. Provide a complete answer that ends with a single period '.' as the final character."
    return (
        False,
        "The response must end with a period. Ensure the final visible character is '.'. "
        "Do not place quotes, parentheses, emojis, or other characters after the period. "
        "Example of a correct ending: '... km/h.'"
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response includes the exact identifier 'km/h'.
    Requirement: The substring 'km/h' must appear at least once (case-sensitive).
    """
    if not isinstance(response, str):
        return False, "The response must be a string. Include the exact identifier 'km/h' in the text."

    if REQUIRED_IDENTIFIER in response:
        return True, "Pass: The response includes the required identifier 'km/h'."
    return (
        False,
        "The response must include the exact identifier 'km/h' at least once. "
        "Do not use variations such as 'kph', 'kmh', or 'KM/H'. "
        "Insert it alongside the relevant numeric value, e.g., 'Average wind speed: 12 km/h.'"
    )

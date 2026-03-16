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
Rank the following from smallest to largest: (a) the annual number of visitors to the museum in the city where the inventor of the telephone was born, (b) the amount of rainfall in millimeters over a year in the region famous for its vineyards, and (c) the number of species inhabiting the coral reef known for its biodiversity. The answer must end with a period. The AI Agent must use the provided tools. If the agent intends to invoke tools, at least two must be selected in a single action from (museum_locator, climate_data_retriever, and biodiversity_database). The task must be completed within a maximum of 10 interaction turns. All information must be obtained via tool calls, and the Agent must self-correct if any tool call fails.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
"""

from typing import Tuple, Optional


def _last_non_whitespace_char(text: str) -> Optional[str]:
    """
    Return the last non-whitespace character of the given text, or None if not found.
    """
    if text is None:
        return None
    stripped = text.rstrip()
    if not stripped:
        return None
    return stripped[-1]


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.'.

    Rules:
    - The final non-whitespace character of the entire response must be a period '.'.

    Returns:
    - (True, message) if valid.
    - (False, message) with actionable guidance if invalid.
    """
    last_char = _last_non_whitespace_char(response)
    if last_char == '.':
        return True, "Valid: The response ends with a period '.' as required."
    if last_char is None:
        return (
            False,
            "Invalid: The response is empty or whitespace only. Provide the final answer and ensure the very last non-whitespace character is a period '.'. For example: 'A < B < C.'."
        )
    return (
        False,
        f"Invalid: The final non-whitespace character is '{last_char}', not a period '.'. "
        "Revise your output so that the entire response ends with a period and no characters follow it. "
        "If your answer spans multiple lines or sections, ensure the very last character of the full response is '.'. "
        "Example: 'Ranked order: (a) < (c) < (b).'"
    )

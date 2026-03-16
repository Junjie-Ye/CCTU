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
 If the agent chooses to execute the tools, they must be called in the following specific order: urban_feature_locator, commercial_district_locator, business_locator, service_relationship_finder, mall_management_locator, footfall_analyzer. The solution must be completed in at most 8 interaction rounds. The response must end with a period.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', '"The response must end with a period (.) to ensure proper sentence closure."')
"""

from typing import Tuple


def _last_non_whitespace_char(s: str) -> str:
    """
    Return the last non-whitespace character of the string, or empty string if none.
    """
    if not isinstance(s, str):
        return ""
    s = s.rstrip()
    return s[-1] if s else ""


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Punctuation constraint:
    The response must end with a period (.) to ensure proper sentence closure.

    Returns:
        - (True, detailed_message) if the response ends with a period.
        - (False, actionable_message) with concrete, step-by-step guidance to fix otherwise.
    """
    if not isinstance(response, str):
        return (
            False,
            "The response is not a string. Provide a string response that ends with a period '.' as the last character."
        )

    trimmed_last = _last_non_whitespace_char(response)

    if trimmed_last == "":
        return (
            False,
            "The response is empty or whitespace-only. Provide a non-empty final answer and ensure the very last character is a period '.'."
        )

    if trimmed_last != ".":
        # Provide precise guidance with the observed last character
        visible = trimmed_last.replace("\n", "\\n").replace("\t", "\\t")
        return (
            False,
            "Invalid ending punctuation: The response must end with a period '.', but it currently ends with '{}'. "
            "Fix it by making the period '.' the final character of the entire output with no trailing spaces. "
            "If your output contains multiple sections (e.g., [THOUGHT], [ACTION], [REFLECTION], [FINAL ANSWER]), "
            "ensure the period appears at the very end of the whole message, after any closing brackets or quotes. "
            "Example fix: append a single '.' at the end of the response and remove any trailing whitespace.".format(
                visible)
        )

    return (
        True,
        "Valid: The response ends with a period '.' as the last non-whitespace character. No changes needed."
    )

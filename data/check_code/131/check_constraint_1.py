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
 You must complete this task in a number of interaction turns that falls between 1 and 3, inclusive. Additionally, your response must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
"""

from typing import Tuple

# Helper: characters that may legally trail the final period (e.g., closing quotes/brackets)
_CLOSING_TRAILERS = '")]}»›”’〉》)]】\''


def _ends_with_period_allowing_trailers(response: str) -> bool:
    """
    Returns True if the response ends with a period '.', allowing trailing closing
    quotes/brackets after the period. Trailing whitespace is ignored.
    Examples considered valid:
      - "This is fine."
      - "He said, 'done.'"
      - "Result.)"
      - "Quote.”"
    """
    if not isinstance(response, str):
        return False
    s = response.rstrip()
    if not s:
        return False
    # Strip trailing closing quotes/brackets
    i = len(s) - 1
    while i >= 0 and s[i] in _CLOSING_TRAILERS:
        i -= 1
    if i < 0:
        return False
    return s[i] == '.'


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period, ignoring trailing whitespace
    and allowing closing quotes/brackets after the period.

    Returns:
      (True, detailed_message) if valid,
      (False, detailed_message) with actionable guidance if invalid.
    """
    if _ends_with_period_allowing_trailers(response):
        return True, "Pass: The response ends with a period ('.') as required. Ensure no extra content appears after the period except optional closing quotes or brackets."
    return (
        False,
        "Fail: The response must end with a period. Make the final non-whitespace character a '.' (the period should appear before any closing quotes or brackets). "
        "Example fix: If you wrote He said, \"Done\", change it to He said, \"Done.\" "
        "If the response ends with '!' or '?', replace it with a period. Do not add any extra text after the period."
    )

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
 The response must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', '"Ending punctuation (.)"')
"""

from typing import Tuple

# Set of common trailing "closer" characters that may legally appear
# after the final period (e.g., quotes, brackets). We ignore these
# when checking the required ending period.
TRAILING_CLOSERS = set(['"', "'", ")", "]", "}", "›",
                       "»", "”", "’", "」", "』", ")", "]", "}", ">", "›"])


def _last_content_char(response: str) -> Tuple[int, str]:
    """
    Returns the index and character of the last non-closer, non-whitespace character.
    If none is found, returns (-1, "").
    """
    if response is None:
        return -1, ""
    i = len(response) - 1
    # Strip trailing whitespace first
    while i >= 0 and response[i].isspace():
        i -= 1
    # Then strip closing characters (quotes/brackets)
    while i >= 0 and response[i] in TRAILING_CLOSERS:
        i -= 1
        # Also skip any whitespace between closers (rare but possible)
        while i >= 0 and response[i].isspace():
            i -= 1
    if i < 0:
        return -1, ""
    return i, response[i]


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates the 'punctuation' response constraint:
    - The response must end with a period (.) for proper sentence closure.
    - Trailing closing quotes/brackets after the period are allowed,
      e.g., ...device." is acceptable because the period appears immediately
      before the closing quote.
    Returns:
      (True, message) if valid
      (False, detailed guidance) if invalid
    """
    if response is None or len(response.strip()) == 0:
        return (
            False,
            "The response is empty. Produce a final answer that ends with a period ('.')."
        )

    idx, ch = _last_content_char(response)
    if idx == -1:
        return (
            False,
            "Only closing quotes/brackets or whitespace were found. Add a sentence that ends with a period ('.')."
        )

    if ch == ".":
        return (
            True,
            "Valid: The response ends with a period ('.') when ignoring trailing closing quotes/brackets. No change needed."
        )

    # Build targeted guidance based on the final character
    if ch in {"!", "?"}:
        return (
            False,
            "The response ends with '{}' instead of a period. Replace the final punctuation with a single period ('.'). "
            "If the answer uses closing quotes or brackets, place the period immediately before the closing character. "
            "Examples: 'There are 12 photos.' or 'There are 12 photos.'\"".format(
                ch)
        )
    else:
        # Ends with a letter/number or other non-period character
        return (
            False,
            "The response does not end with a period. Append a single period ('.') at the end of the final sentence. "
            "If your answer ends with a closing quote or bracket, insert the period immediately before it. "
            "Examples: 'There are 12 photos.' or 'There are 12 photos.\"'"
        )

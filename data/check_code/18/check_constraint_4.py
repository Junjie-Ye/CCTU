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
 You must retrieve all information by calling the provided tools, not through internal knowledge. If a tool call fails, correct the parameters and retry until success. You may invoke multiple tools in parallel but must strictly limit the use of the historical_event_finder tool to at most 1 call during the task. The total number of interaction turns must fall within the range of 1 to 3 inclusive. The response must end with a period and include a semicolon after the date to separate it from the context.

response_constraints_non_length:
- idx 2: ('Response', 'Punctuation', 'Ending punctuation (.)')
- idx 4: ('Response', 'Identifiers', 'Must include a semicolon after the date to separate it from the context')
"""

import re
from typing import Tuple, Optional, Pattern, Match

# Precompile common date patterns we will recognize.
# 1) ISO-like: YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
ISO_DATE_PATTERN: Pattern = re.compile(
    r"\b\d{4}[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])\b"
)

# 2) Month D, YYYY (e.g., January 5, 2026 or Jan 5, 2026; comma optional)
MONTH_D_YYYY_PATTERN: Pattern = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(?:0?[1-9]|[12]\d|3[01]),?\s+\d{4}\b",
    re.IGNORECASE,
)

# 3) D Month YYYY (e.g., 5 January 2026 or 05 Jan 2026; comma optional)
D_MONTH_YYYY_PATTERN: Pattern = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?),?\s+\d{4}\b",
    re.IGNORECASE,
)

DATE_PATTERNS = [ISO_DATE_PATTERN, MONTH_D_YYYY_PATTERN, D_MONTH_YYYY_PATTERN]


def _find_first_date(response: str) -> Optional[Match]:
    """
    Find the first date occurrence in the response using supported patterns.
    Returns the regex match object or None if not found.
    """
    earliest_match: Optional[Match] = None
    earliest_start: Optional[int] = None

    for pattern in DATE_PATTERNS:
        match = pattern.search(response)
        if match:
            if earliest_match is None or match.start() < earliest_start:
                earliest_match = match
                earliest_start = match.start()
    return earliest_match


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the response ends with a period '.' as the final character.
    """
    if response is None:
        return (
            False,
            "Response is None. Provide a non-empty string that ends with a period '.' as the final character.",
        )

    stripped = response.rstrip()
    if not stripped:
        return (
            False,
            "The response is empty or whitespace only. Provide a complete answer that ends with a period '.' as the final character.",
        )

    if stripped[-1] != ".":
        return (
            False,
            "The response must end with a period '.' as the final character, with no trailing characters after it. "
            "Edit the output so the last non-whitespace character is a single period. "
            "Example: '2026-01-19; <context>.'",
        )

    return True, "Pass: The response ends with a period '.' as required."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response includes a semicolon ';' immediately after the date
    (allowing only optional spaces between the date and the semicolon) to separate it from the context.
    Also provides guidance if no recognizable date is present.
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. Include a clear date followed by a semicolon ';' (e.g., '2026-01-19; <context>.').",
        )

    date_match = _find_first_date(response)
    if not date_match:
        return (
            False,
            "No recognizable date was found. Start the final answer with a clear date, then a semicolon ';', "
            "then the context, and ensure the entire response ends with a period. "
            "Accepted date formats include: YYYY-MM-DD, Month D, YYYY, or D Month YYYY. "
            "Examples: '2026-01-19; <context>.' or 'Jan 19, 2026; <context>.'",
        )

    # Check for semicolon immediately after the date (allowing only spaces)
    end = date_match.end()
    i = end
    n = len(response)

    # Skip spaces between date and semicolon
    while i < n and response[i].isspace():
        i += 1

    if i >= n or response[i] != ";":
        found_date = response[date_match.start():date_match.end()]
        return (
            False,
            f"A date was detected ('{found_date}'), but no semicolon ';' appears immediately after it "
            "(only optional spaces are allowed before the semicolon). Insert ';' right after the date, "
            "optionally followed by a single space, then continue with the context. "
            f"Example: '{found_date}; <context>.'",
        )

    return True, "Pass: A date is present and is immediately followed by a semicolon ';' to separate it from the context."

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
 You must solve this by calling the provided tools, the total number of tool calls you make must be between 1 and 3, you must use at most one call to the `historical_event_retriever` tool, your final answer must be formatted using Markdown syntax, including proper use of bold text for the date (e.g., **target date**) to highlight the ruling date, your response must end with a period, and your final response must not exceed 100 characters to ensure clarity and brevity.

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'The final answer must be formatted using Markdown syntax, including proper use of bold text for the date (e.g., **May 24, 2024**) to highlight the ruling date.')
- idx 2: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period to ensure proper sentence closure.)')
"""

import re
from typing import Tuple, List

# Precompiled regex for a "Month Day, Year" date with full month name and optional leading zero for day.
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
)

# Month D, YYYY
BOLDED_DATE_PATTERN = re.compile(
    rf"^\s*(?:{MONTHS})\s+(0?[1-9]|[12][0-9]|3[01]),\s+\d{{4}}\s*$"
)

# ISO: YYYY-MM-DD
ISO_DATE_PATTERN = re.compile(
    r"^\s*\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\s*$"
)

BOLD_SEGMENT_FINDER = re.compile(r"\*\*(.+?)\*\*")


def _extract_bold_segments(text: str) -> List[str]:
    return BOLD_SEGMENT_FINDER.findall(text or "")


def validate_format(response: str) -> Tuple[bool, str]:
    if not response or not response.strip():
        return (
            False,
            "Response is empty. Provide a Markdown-formatted sentence containing a bolded date."
        )

    star_pairs_count = response.count("**")
    if star_pairs_count % 2 != 0:
        return (
            False,
            "Unbalanced Markdown bold markers. Ensure every ** has a matching closing **."
        )

    bold_segments = _extract_bold_segments(response)
    if not bold_segments:
        return (
            False,
            "No Markdown bold text found. Add the ruling date in bold, e.g., **May 24, 2024** or **2024-03-12**."
        )

    has_bold_date = any(
        BOLDED_DATE_PATTERN.match(seg) or ISO_DATE_PATTERN.match(seg)
        for seg in bold_segments
    )

    if not has_bold_date:
        return (
            False,
            "No valid bolded date detected. Include at least one bold segment that is exactly a date in either "
            "**Month D, YYYY** (e.g., **May 24, 2024**) or **YYYY-MM-DD** (e.g., **2024-03-12**)."
        )

    return (
        True,
        "Valid: Found a Markdown-bolded date."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    Trailing whitespace after the period is allowed, but the last non-whitespace character must be '.'.
    """
    if not response or not response.strip():
        return (
            False,
            "Response is empty. Provide a single concise sentence ending with a period."
        )

    trimmed = response.rstrip()
    if not trimmed or trimmed[-1] != ".":
        return (
            False,
            "The response must end with a period. Add a '.' as the final character (whitespace may follow it)."
        )

    return (
        True,
        "Valid: The response ends with a period."
    )

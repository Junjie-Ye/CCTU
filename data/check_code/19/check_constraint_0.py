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
 Your response must end with the exact phrase "Casualties: **X**", where X is the numerical answer. Additionally, you must ensure that the 'historical_event_data_retriever' tool is used no more than once to obtain this information.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Response, End identifier, The response must conclude with the exact phrase "Casualties: **X**", where X is the numerical answer, ensuring a clear and consistent ending.)')
"""

import re
from typing import Tuple, Optional

# Pre-compiled regex for the exact required ending:
# Must be: Casualties: **X** where X is a non-negative integer, optionally with proper comma grouping.
_REQUIRED_ENDING_RE = re.compile(
    r'Casualties: \*\*(\d{1,3}(?:,\d{3})*|\d+)\*\*$')


def _extract_last_number(text: str) -> Optional[str]:
    """
    Extract the last numeric token in the text.
    Accepts either plain digits or properly grouped thousands with commas.
    Returns the string form of the number if found, otherwise None.
    """
    matches = re.findall(r'\d{1,3}(?:,\d{3})*|\d+', text)
    return matches[-1] if matches else None


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the exact phrase:
    Casualties: **X**
    where X is a numeric answer (non-negative integer, optionally with comma separators).
    There must be no characters (including spaces or newlines) after the closing '**'.
    """
    # Direct exact-match check at true end of string
    if _REQUIRED_ENDING_RE.search(response):
        return (
            True,
            "OK: The response correctly ends with the exact phrase 'Casualties: **X**' using a numeric value and no trailing content."
        )

    # If it would match after trimming trailing whitespace, guide removal of trailing whitespace
    trimmed = response.rstrip()
    if trimmed != response and _REQUIRED_ENDING_RE.search(trimmed):
        return (
            False,
            "Your response ends correctly before trailing whitespace, but it must end with the exact phrase with no characters after it. "
            "Trim any spaces or newline characters after the final '**' so the last characters are exactly: Casualties: **<number>**."
        )

    # Provide targeted guidance and a concrete suggestion if a number is present
    last_num = _extract_last_number(response)

    guidance = [
        "Your response must end with exactly: Casualties: **X**",
        "Requirements:",
        "- 'Casualties' must be capitalized exactly as shown.",
        "- Use a colon followed by a single space: ': '.",
        "- Wrap the numeric answer in double asterisks: **<number>**.",
        "- The number must be a non-negative integer (commas allowed, e.g., 1,234).",
        "- Place nothing (no spaces or newlines) after the closing '**'.",
        "Example: Casualties: **123**"
    ]

    if last_num is not None:
        suggestion = f"Suggested fix based on detected number '{last_num}': end your message with exactly: Casualties: **{last_num}**"
    else:
        suggestion = "If you know the numeric answer X, end your message with exactly: Casualties: **X**"

    return (
        False,
        "Invalid ending. " + " ".join(guidance) + " " + suggestion
    )

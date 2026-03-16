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
 The response must end with the phrase "Total: [number] operas combined., where [number] is replaced by the actual sum calculated from tool responses. The solution must be completed in at most 3 interaction turns with the tools. The final answer must contain between 30 and 60 words to ensure sufficient detail while maintaining conciseness.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "Must end with the phrase 'Total: [number] operas combined., where [number] is replaced by the actual sum calculated from tool responses.")
"""

import re
from typing import Tuple

# Helper regex patterns for diagnostics
_PATTERN_END_EXACT = re.compile(r"Total:\s*(\d+)\s+operas\s+combined\.$")
_PATTERN_NO_PERIOD = re.compile(r"Total:\s*\d+\s+operas\s+combined$")
_PATTERN_SINGULAR_OPERA = re.compile(r"Total:\s*\d+\s+opera\s+combined\.?$")
_PATTERN_WITH_PERIOD_ANYWHERE = re.compile(
    r"(Total:\s*\d+\s+operas\s+combined\.)")
_PATTERN_ANY_TOTAL = re.compile(r"Total\s*:?", re.IGNORECASE)


def _rstrip(s: str) -> str:
    return s.rstrip("\n\r\t ").rstrip()


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends exactly with:
    'Total: [number] operas combined.'
    - [number] must be an Arabic numeral (digits).
    - The phrase must be the final text (no characters after the period).
    - Exact words: 'Total:' then number, 'operas combined.'
    - Case-sensitive 'Total' and includes the colon.
    - Trailing whitespace is allowed but ignored during validation.
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string. End the message with: 'Total: [number] operas combined.' using digits for [number]."
        )

    text = _rstrip(response)

    # Exact correct ending
    m = _PATTERN_END_EXACT.search(text)
    if m and m.end() == len(text):
        n_str = m.group(1)
        return (
            True,
            f"OK. Found required ending with number {n_str}. Keep the exact ending: 'Total: {n_str} operas combined.'"
        )

    # Diagnostics and targeted guidance
    # 1) Phrase present but followed by extra text
    m_anywhere = _PATTERN_WITH_PERIOD_ANYWHERE.search(text)
    if m_anywhere and m_anywhere.end() != len(text):
        return (
            False,
            "Move the phrase to the very end and remove any trailing text. The final characters must be exactly: 'Total: [number] operas combined.'"
        )

    # 2) Missing final period
    if _PATTERN_NO_PERIOD.search(text):
        return (
            False,
            "Add a final period. The response must end exactly with: 'Total: [number] operas combined.'"
        )

    # 3) Singular 'opera' instead of 'operas'
    if _PATTERN_SINGULAR_OPERA.search(text):
        return (
            False,
            "Use the plural form 'operas'. End with: 'Total: [number] operas combined.'"
        )

    # 4) 'Total' present but formatting issues (e.g., missing colon, wrong case, non-digit number)
    if _PATTERN_ANY_TOTAL.search(text):
        # Check colon after 'Total'
        if not re.search(r"Total:\s*\d+", text):
            return (
                False,
                "Place a colon after 'Total' and use digits for the number. Correct form: 'Total: [number] operas combined.'"
            )
        # Check digits for number
        if not re.search(r"Total:\s*\d+\s+operas\s+combined\.?$", text):
            return (
                False,
                "Use Arabic digits and exact wording. Required ending: 'Total: [number] operas combined.'"
            )

    # 5) Generic failure guidance
    return (
        False,
        "The response must end exactly with: 'Total: [number] operas combined.' Use digits for [number], include the colon after 'Total', the plural 'operas', and a final period. No text is allowed after this phrase."
    )

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
 Your answer must be formatted using Markdown syntax and include the date in bold.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must be formatted using Markdown syntax, including a clearly marked date in bold.')
"""

import re
from typing import Tuple, List, Pattern

# Precompile regex patterns for supported date formats inside bold markers.
# The response must be ONLY a bolded date, with no additional text or formatting.
# Accepted date formats (with leading zeros where applicable):
# - MM/YYYY           e.g., 07/2008
# - YYYY-MM           e.g., 2008-07
# - YYYY-MM-DD        e.g., 2008-07-15
# - DD/MM/YYYY        e.g., 15/07/2008
# - YYYY/MM/DD        e.g., 2008/07/15
# - MM-DD-YYYY        e.g., 07-15-2008
DATE_PATTERNS: List[Tuple[Pattern, str]] = [
    (re.compile(r'^(0[1-9]|1[0-2])/[12][0-9]{3}$'), 'MM/YYYY (e.g., 07/2008)'),
    (re.compile(r'^[12][0-9]{3}-(0[1-9]|1[0-2])$'), 'YYYY-MM (e.g., 2008-07)'),
    (re.compile(r'^[12][0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'),
     'YYYY-MM-DD (e.g., 2008-07-15)'),
    (re.compile(
        r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[12][0-9]{3}$'), 'DD/MM/YYYY (e.g., 15/07/2008)'),
    (re.compile(r'^[12][0-9]{3}/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])$'),
     'YYYY/MM/DD (e.g., 2008/07/15)'),
    (re.compile(
        r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])-[12][0-9]{3}$'), 'MM-DD-YYYY (e.g., 07-15-2008)'),
]

# Matches a response that is ONLY a single Markdown bold segment (**...** or __...__), allowing surrounding whitespace.
BOLD_ONLY_PATTERN = re.compile(
    r'^\s*(?:\*\*(?P<inner_star>.+?)\*\*|__(?P<inner_underscore>.+?)__)\s*$')


def _extract_bold_inner(response: str) -> Tuple[bool, str]:
    """
    Helper to verify the response is exactly one bold segment and return its inner text.
    Returns (ok, inner_text_or_error).
    """
    if not response or response.strip() == '':
        return False, "Response is empty. Output must be exactly one bolded date in Markdown, e.g., **07/2008**."

    if '```' in response:
        return False, "Do not use code blocks. The output must be only a bolded date, e.g., **07/2008**."

    m = BOLD_ONLY_PATTERN.match(response)
    if not m:
        return False, (
            "Invalid format. The response must contain ONLY a single bold segment with the date and nothing else. "
            "Use **date** or __date__ with no additional text, headings, lists, or punctuation outside the bold."
        )

    inner = m.group('inner_star') or m.group('inner_underscore') or ''
    inner_stripped = inner.strip()

    if not inner_stripped:
        return False, "Bold content is empty. Place a valid date inside the bold markers, e.g., **07/2008**."

    if '\n' in inner or '\r' in inner:
        return False, "Bolded date must be on a single line. Remove line breaks inside the bold markers."

    return True, inner_stripped


def _matches_supported_date(inner: str) -> bool:
    for pattern, _desc in DATE_PATTERNS:
        if pattern.match(inner):
            return True
    return False


def _supported_formats_hint() -> str:
    fmts = [desc for _pat, desc in DATE_PATTERNS]
    return "Supported date formats: " + "; ".join(fmts) + "."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response:
    - Is strictly Markdown with ONLY a bolded date (no other text or formatting).
    - The bolded content matches one of the supported date formats.

    Returns:
        (True, success_message) if valid,
        (False, detailed_instruction) if invalid.
    """
    ok, inner_or_err = _extract_bold_inner(response)
    if not ok:
        return False, inner_or_err

    inner = inner_or_err
    if not _matches_supported_date(inner):
        return False, (
            "The bolded content is not recognized as a valid date. "
            "Provide ONLY a bolded date with leading zeros where applicable (e.g., **07/2008**). "
            + _supported_formats_hint()
        )

    return True, "Format is valid: response contains only a bolded date in Markdown (e.g., **07/2008**)."

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
 The agent must obtain the answer by calling tools, is permitted to invoke the 'individual_movement_tracker' tool at most 2 times during the task, must complete the task within a maximum of 3 total interaction turns, the final response must not exceed 100 characters in length, must end with a period, and must be formatted using Markdown syntax with at least one bold text element.

response_constraints_non_length:
- idx 3: ('Response', 'Punctuation', 'Must end with a period')
- idx 4: ('Response', 'Format', '(Response, Format, Must be formatted using Markdown syntax with at least one bold text element)')
"""

import re
from typing import Tuple

# ---------------------------
# Helper utilities
# ---------------------------

WHITESPACE_RE = re.compile(r'\s+\Z', re.MULTILINE)

# Bold detection patterns:
# - **bold** (not allowing only whitespace inside)
# - __bold__ (not allowing only whitespace inside)
BOLD_PATTERNS = [
    re.compile(r'(?<!\*)\*\*(?=\S)(.+?)(?<=\S)\*\*(?!\*)', re.DOTALL),
    re.compile(r'(?<!_)__(?=\S)(.+?)(?<=\S)__(?!_)', re.DOTALL),
]


def _ends_with_period(text: str) -> bool:
    """Check if the last non-whitespace character is a '.' (ASCII dot)."""
    trimmed = WHITESPACE_RE.sub("", text)
    return trimmed.endswith(".")


def _contains_markdown_bold(text: str) -> bool:
    """Return True if text contains at least one Markdown bold segment."""
    return any(p.search(text) is not None for p in BOLD_PATTERNS)

# ---------------------------
# Validators
# ---------------------------


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Constraint: Must end with a period.
    Returns:
      - bool: True if compliant, else False
      - str: Detailed English guidance to fix issues
    """
    if not response or not _ends_with_period(response):
        return (
            False,
            "The response must end with a period. Ensure the last non-whitespace character is a '.' "
            "(ASCII dot). If it does not end with '.', append a single period at the very end, after "
            "all Markdown or text. Example: '**Result**.'"
        )
    return (
        True,
        "Punctuation OK: The response ends with a period."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Constraint: Must be formatted using Markdown syntax with at least one bold text element.
    Returns:
      - bool: True if compliant, else False
      - str: Detailed English guidance to fix issues
    """
    if not response:
        return (
            False,
            "The response is empty. Provide Markdown-formatted content that includes at least one "
            "bold element using **bold text** or __bold text__."
        )

    if not _contains_markdown_bold(response):
        return (
            False,
            "Add at least one Markdown bold element. Use **bold text** or __bold text__. "
            "Do not escape the markers, and wrap non-whitespace characters with matching pairs. "
            "Example: '**Answer**: data.'"
        )

    return (
        True,
        "Format OK: The response includes Markdown with at least one bold element."
    )

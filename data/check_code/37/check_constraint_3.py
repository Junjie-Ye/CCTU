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
 Your response must be formatted using Markdown syntax with appropriate elements like headings or bold text to enhance clarity. The answer must be retrieved via the earthquake_event_retriever tool no more than once. The solution must not require more than 2 total tool calls across all interaction steps. Your final response must include the exact phrase "Earthquake Magnitude: [magnitude value]" where [magnitude value] is replaced with the numeric magnitude retrieved from the tool, and must conclude with a period as the final punctuation mark.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Response, End identifier, "The final answer must include the exact phrase \'Earthquake Magnitude: [magnitude value]\' where [magnitude value] is replaced with the numeric magnitude retrieved from the tool response.")')
- idx 2: ('Response', 'Punctuation', 'Ending punctuation (.)')
- idx 3: ('Response', 'Format', '(Response, Format, "The agent\'s entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.")')
"""

import re
from typing import Tuple

# -----------------------------------------------------------------------------
# Markdown feature detectors (broad + tolerant)
# -----------------------------------------------------------------------------
HEADING_RE = re.compile(r'^\s{0,3}#{1,6}\s+\S',
                        re.MULTILINE)                    # # Title
# - item / 1. item
LIST_RE = re.compile(r'^\s{0,3}(?:[-*+]\s+|\d+\.\s+)\S', re.MULTILINE)
# **...** or __...__
BOLD_RE = re.compile(r'(\*\*.+?\*\*|__.+?__)', re.DOTALL)
ITALIC_RE = re.compile(
    r'(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)')        # *...* or _..._
# `code`
INLINE_CODE_RE = re.compile(r'`[^`\n]+`')
# ```
CODE_FENCE_RE = re.compile(r'```')
# [text](url)
LINK_RE = re.compile(r'\[[^\]]+\]\([^)]+\)')

# Required identifier phrase pattern
MAGNITUDE_PATTERN = re.compile(
    r'\bEarthquake Magnitude:\s*(-?\d+(?:\.\d+)?)\b')


def _has_balanced_code_fences(text: str) -> bool:
    """Require fenced code blocks to be balanced if present."""
    return len(CODE_FENCE_RE.findall(text)) % 2 == 0


def _has_any_markdown_feature(text: str) -> bool:
    """
    Minimal Markdown requirement: if ANY Markdown feature is present, accept.
    (No requirement that heading must be first line, and no requirement for multiple elements.)
    """
    return any([
        bool(HEADING_RE.search(text)),
        bool(LIST_RE.search(text)),
        bool(BOLD_RE.search(text)),
        bool(ITALIC_RE.search(text)),
        bool(INLINE_CODE_RE.search(text)),
        bool(CODE_FENCE_RE.search(text)),
        bool(LINK_RE.search(text)),
    ])

# -----------------------------------------------------------------------------
# Validators
# -----------------------------------------------------------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Constraint intent: "response must be formatted using Markdown syntax"
    Minimal enforcement:
      - Must contain at least ONE Markdown feature (heading/list/bold/italic/link/inline code/code fence).
      - If code fences are used, they must be balanced.
    """
    if response is None or not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty. Provide a non-empty answer that includes at least one Markdown element "
            "(e.g., a heading, list, bold/italic, link, inline code, or fenced code block)."
        )

    if not _has_any_markdown_feature(response):
        return (
            False,
            "No Markdown features detected. Include at least one Markdown element such as: "
            "# heading, - list item, **bold**, *italic*, [link](https://example.com), `inline code`, or ```fenced code```."
        )

    if not _has_balanced_code_fences(response):
        return (
            False,
            "Unbalanced fenced code blocks detected. If you use ``` to start a code block, close it with another ```."
        )

    return (True, "Markdown detected (at least one Markdown feature present).")


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Final punctuation must be a period '.' as the last non-whitespace character.
    """
    if response is None or not isinstance(response, str) or not response.strip():
        return (False, "The response is empty. It must end with a period '.'.")

    trimmed = response.rstrip()
    if not trimmed.endswith("."):
        return (
            False,
            "Ensure the last non-whitespace character in the response is a period '.'."
        )

    return (True, "The response ends with a period.")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Must include the exact phrase pattern:
      'Earthquake Magnitude: <number>'
    where <number> is numeric (int/float, optional leading '-').
    """
    if response is None or not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty. Include 'Earthquake Magnitude: <number>' with a numeric magnitude."
        )

    # Disallow placeholder with brackets (optional strictness; keep for clarity)
    if re.search(r'\bEarthquake Magnitude:\s*\[', response):
        return (
            False,
            "Replace the placeholder with a numeric value and remove brackets. "
            "Example: 'Earthquake Magnitude: 5.2'."
        )

    m = MAGNITUDE_PATTERN.search(response)
    if not m:
        # case-sensitive guidance
        if re.search(r'earthquake magnitude:', response, flags=re.IGNORECASE) and 'Earthquake Magnitude:' not in response:
            return (
                False,
                "Use the exact case-sensitive prefix 'Earthquake Magnitude:' followed by a number, e.g., "
                "'Earthquake Magnitude: 5.2'."
            )
        return (
            False,
            "Include the exact phrase 'Earthquake Magnitude: <number>' (e.g., 'Earthquake Magnitude: 5.2')."
        )

    # Ensure no letters immediately attached to the number (e.g., 5.2Mw)
    end_index = m.end(1)
    if end_index < len(response) and response[end_index].isalnum():
        return (
            False,
            "Do not attach letters/units directly to the magnitude number. Use 'Earthquake Magnitude: <number>'."
        )

    return (True, "Identifier phrase with numeric magnitude detected.")

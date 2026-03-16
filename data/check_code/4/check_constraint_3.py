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
 The answer must be formatted using Markdown syntax, including the use of bold text to emphasize the location. The solution must require between 2 and 5 interaction turns (inclusive). The answer must not exceed 50 words in total length and must end with the identifier "END". You may call the event_locator tool at most 2 times during the process.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 3: ('Response', 'Identifiers', "(Response, End identifier, The answer must end with the identifier 'END' (Mandates that the agent's response must conclude with a specific identifier or phrase, providing a clear and consistent ending.))")
"""

import re
from typing import Tuple

# Helper regex patterns for Markdown detection
RE_HEADING = re.compile(r'^\s{0,3}#{1,6}\s+\S', re.MULTILINE)
RE_LIST = re.compile(r'^\s{0,3}(?:[-*+]|[0-9]+\.)\s+\S', re.MULTILINE)
RE_LINK = re.compile(r'\[[^\]]+\]\([^)]+\)')
RE_INLINE_CODE = re.compile(r'`[^`]+`')
RE_BOLD = re.compile(r'(\*\*[^*\n]+\*\*|__[^_\n]+__)')
RE_BLOCKQUOTE = re.compile(r'^\s{0,3}>\s+\S', re.MULTILINE)
RE_TABLE_PIPE = re.compile(r'^\s*\|.*\|\s*$', re.MULTILINE)


def _count_occurrences(text: str, token: str) -> int:
    """Count non-overlapping occurrences of a token."""
    return text.count(token)


def _has_balanced_fences(text: str) -> bool:
    """Ensure triple backtick code fences are balanced."""
    return _count_occurrences(text, "```") % 2 == 0


def _has_balanced_delimiter(text: str, delim: str) -> bool:
    """Ensure a delimiter appears an even number of times (rough heuristic)."""
    return _count_occurrences(text, delim) % 2 == 0


def _contains_any_markdown_structure(text: str) -> bool:
    """Heuristic: detect presence of common Markdown elements."""
    return any([
        bool(RE_HEADING.search(text)),
        bool(RE_LIST.search(text)),
        bool(RE_LINK.search(text)),
        bool(RE_INLINE_CODE.search(text)),
        bool(RE_BLOCKQUOTE.search(text)),
        bool(RE_TABLE_PIPE.search(text)),
        bool(RE_BOLD.search(text)),  # bold also counts
        "```" in text,               # code fence presence
    ])


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response uses Markdown syntax (heuristic: contains at least one Markdown element).
    - Bold formatting is present to emphasize the location (**text** or __text__).
    - Markdown fences/delimiters that commonly cause rendering issues are balanced.
    """
    if not response or not response.strip():
        return (False, "Empty response. Provide a Markdown-formatted answer with at least one Markdown element and include bold emphasis for the location using **...** or __...__.")

    # Require bold emphasis for location
    has_bold = bool(RE_BOLD.search(response))
    if not has_bold:
        return (False, "Missing bold emphasis. Use **bold** or __bold__ to highlight the location. Example: The event occurred in **City, Country**.")

    # Ensure general Markdown presence (bold counts, but additional elements are allowed)
    if not _contains_any_markdown_structure(response):
        return (False, "No detectable Markdown elements. Add at least one Markdown feature (e.g., a heading '# Title', a list '- item', a link [text](url), code `inline`, or bold **text**).")

    # Balanced code fences
    if not _has_balanced_fences(response):
        return (False, "Unbalanced code fences detected. Ensure the number of triple backticks ``` is even and fences are properly opened and closed.")

    # Balanced bold delimiters (heuristic)
    if not _has_balanced_delimiter(response, "**") or not _has_balanced_delimiter(response, "__"):
        return (False, "Unbalanced bold delimiters detected. Make sure ** and __ appear in pairs around the emphasized text, e.g., **Location**.")

    return (True, "Format validation passed. The response includes Markdown with bold emphasis and has balanced fences/delimiters.")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the exact identifier 'END'.
    Trailing whitespace after END is allowed; any other trailing characters are not.
    """
    if response is None:
        return (False, "Response is None. Provide a string that ends with the identifier END.")

    trimmed = response.rstrip()  # allow trailing whitespace
    if not trimmed.endswith("END"):
        return (False, "The response must end with the exact identifier END. Place END as the very last characters (no punctuation or text after it). Example:\n\n... final sentence.\nEND")

    return (True, "Identifier validation passed. The response ends with END.")

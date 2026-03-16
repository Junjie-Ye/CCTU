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
 The answer must be concise, contain at most 15 words, start with the phrase "The main export product is", and be formatted using Markdown syntax with proper use of bold/italic text to highlight key information.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of bold/italic text to highlight key information)")
- idx 2: ('Response', 'Identifiers', 'Must start with the phrase "The main export product is" followed by the answer in bold using Markdown syntax.')
"""

import re
from typing import Tuple

# Helper regex patterns
BOLD_MD_PATTERN = re.compile(
    r"(\*\*(?=\S).+?(?<=\S)\*\*|__(?=\S).+?(?<=\S)__)")
ITALIC_MD_PATTERN = re.compile(
    r"(?<!\*)\*(?=\S)(.+?)(?<=\S)\*(?!\*)|(?<!_)_(?=\S)(.+?)(?<=\S)_(?!_)")
HTML_EMPHASIS_PATTERN = re.compile(r"</?(b|i|strong|em)\b", re.IGNORECASE)

# Helper functions


def _has_markdown_emphasis(text: str) -> bool:
    """Return True if the text contains at least one Markdown bold or italic span."""
    return bool(BOLD_MD_PATTERN.search(text) or ITALIC_MD_PATTERN.search(text))


def _has_unbalanced_emphasis(text: str) -> bool:
    """
    Heuristic check for unbalanced Markdown emphasis markers:
    - Even number of '**' and '__'
    - Remaining single '*' and '_' count should be even (not counting those used in '**' and '__').
    This is a pragmatic validator tailored for short, single-line responses.
    """
    # Count paired markers
    double_star = text.count("**")
    double_underscore = text.count("__")
    if double_star % 2 != 0 or double_underscore % 2 != 0:
        return True

    # Count single markers excluding those consumed by double markers
    total_star = text.count("*")
    total_underscore = text.count("_")
    single_star = total_star - 2 * double_star
    single_underscore = total_underscore - 2 * double_underscore

    # If odd counts remain, emphasis is likely unbalanced
    if single_star % 2 != 0 or single_underscore % 2 != 0:
        return True

    return False


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the 'format' response constraint:
    - The entire response must be valid Markdown with proper emphasis usage.
    - Must include bold and/or italic Markdown to highlight key information.
    - Must not use HTML tags (<b>, <i>, <strong>, <em>) for emphasis.
    - Emphasis markers should be balanced (no stray *, _, **, or __).
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string formatted in Markdown with bold/italic emphasis; received non-string.",
        )

    text = response.strip()
    if not text:
        return (
            False,
            "Response is empty. Provide a Markdown-formatted sentence using **bold** and/or *italic* to highlight key information.",
        )

    if HTML_EMPHASIS_PATTERN.search(text):
        return (
            False,
            "Do not use HTML tags for emphasis. Use Markdown: **bold** or *italic* (also __bold__ or _italic_).",
        )

    if not _has_markdown_emphasis(text):
        return (
            False,
            "Add Markdown emphasis to highlight key information. Example: The main export product is **Widgets**.",
        )

    if _has_unbalanced_emphasis(text):
        return (
            False,
            "Unbalanced Markdown emphasis markers detected. Ensure ** and __ appear in pairs, and single * or _ are properly paired.",
        )

    return True, "Format OK: Markdown detected with proper bold/italic emphasis and no HTML tags."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the 'identifiers' response constraint:
    - The response must start exactly (case-sensitive) with: 'The main export product is'
    - Optionally followed by a colon.
    - Immediately followed by the answer in bold using Markdown (**...** or __...__).
    - No extra non-whitespace content before this phrase.
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string starting with 'The main export product is' followed by a bold answer.",
        )

    # allow leading whitespace but enforce phrase at the actual start
    text = response.lstrip()
    # Pattern: start phrase, optional colon, optional spaces, then bold content; allow trailing whitespace
    pattern = re.compile(
        r'^The main export product is(?::)?\s*(\*\*(?=\S).+?(?<=\S)\*\*|__(?=\S).+?(?<=\S)__)\\s*$'
    )

    # The above pattern with raw string escape for \s*$ may be confusing when embedded. Build safely:
    start_bold_pattern = re.compile(
        r'^The main export product is(?::)?\s*'
        r'(\*\*(?=\S).+?(?<=\S)\*\*|__(?=\S).+?(?<=\S)__)'
        r'(?:[.。])?\s*$'
    )

    if not text.startswith("The main export product is") and not text.startswith("The main export product is:"):
        return (
            False,
            "Start the response exactly with 'The main export product is' (case-sensitive), optionally followed by a colon.",
        )

    if not start_bold_pattern.match(text):
        return (
            False,
            "Immediately after the phrase, provide the answer in bold Markdown. Example:\n"
            "The main export product is **Crude oil**\n"
            "Do not add extra text before or after the bold answer.",
        )

    return True, "Identifiers OK: Response starts with the required phrase and the answer is in bold."

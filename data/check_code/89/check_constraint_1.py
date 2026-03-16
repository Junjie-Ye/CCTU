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
 If the agent invoke 'supplier_hospital_locator' tool, it must call it before the 'hospital_survival_rate_analyzer' tool. The total number of tool calls must be between 5 and 8, inclusive. The final answer must be formatted using Markdown syntax, including proper headings, lists, bold/italic text, and code blocks to enhance readability and structure. Additionally, the final answer must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "The agent's final answer must be formatted using Markdown syntax, including proper headings, lists, bold/italic text, and code blocks to enhance readability and structure.")
- idx 2: ('Response', 'Punctuation', "The agent's final answer must end with a period to ensure proper sentence closure.")
"""

import re
from typing import Tuple

# -----------------------
# Helper utilities
# -----------------------

FENCED_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def strip_fenced_code_blocks(text: str) -> str:
    """Remove fenced code blocks (``` ... ```) from text for pattern checks."""
    return FENCED_BLOCK_RE.sub("", text)


def contains_fenced_code_block(text: str) -> bool:
    """Return True if there is at least one complete fenced code block."""
    return bool(FENCED_BLOCK_RE.search(text))


def has_markdown_heading(text_no_code: str) -> bool:
    """Detect ATX (#) or Setext (= or - underline) headings outside code blocks."""
    atx = re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", text_no_code) is not None
    setext = re.search(r"(?m)^[^\n]+\n[=-]{3,}\s*$", text_no_code) is not None
    return atx or setext


def has_markdown_list(text_no_code: str) -> bool:
    """Detect unordered (-, *, +) or ordered (1.) list items outside code blocks."""
    return re.search(r"(?m)^\s*(?:[-*+]\s+\S|\d+\.\s+\S)", text_no_code) is not None


def has_bold_or_italic(text_no_code: str) -> bool:
    """Detect bold (**...** or __...__) or italic (*...* or _..._) outside code blocks."""
    # Avoid matching empty or whitespace-only content between markers
    bold = re.search(
        r"(\*\*[^*\n][^*\n]*\*\*|__[^_\n][^_\n]*__)", text_no_code) is not None
    italic = re.search(
        r"(\*[^*\n][^*\n]*\*|_[^_\n][^_\n]*_)", text_no_code) is not None
    return bold or italic


def ends_with_period(text: str) -> bool:
    """Check if the final non-whitespace character is a literal period '.'."""
    return text.rstrip().endswith(".")

# -----------------------
# Validators
# -----------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer contains at least ONE of these Markdown elements:
    - A heading
    - A list (ordered or unordered)
    - Bold or italic emphasis
    - A fenced code block (``` ... ```)
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Provide an answer with at least one Markdown element: heading, list, emphasis, or code block."
        )

    text_no_code = strip_fenced_code_blocks(response)

    # Check each element
    has_heading = has_markdown_heading(text_no_code)
    has_list = has_markdown_list(text_no_code)
    has_emphasis = has_bold_or_italic(text_no_code)
    has_code_block = contains_fenced_code_block(response)

    # OR logic: At least one element must be present
    has_any_markdown = has_heading or has_list or has_emphasis or has_code_block

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. A bulleted or numbered list (e.g., '- Item' or '1. Step')\n"
            "3. Bold or italic emphasis (e.g., **important** or *note*)\n"
            "4. A fenced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Build feedback on what was found and missing
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append(
            "- Add a heading (e.g., '# Overview') for structure.")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append("- Add a list (e.g., '- Item') for organization.")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append(
            "- Use emphasis (e.g., **bold** or *italic*) for highlights.")

    if has_code_block:
        found_elements.append("code block")
    else:
        suggestions.append(
            "- Add a complete correct code block (```) for examples or data.")

    # Build response message
    success_msg = f"The response contains {', '.join(found_elements)}."

    if suggestions:
        success_msg += "\n\nSuggestions for improvement:\n" + \
            "\n".join(suggestions)

    return (True, success_msg)


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period '.' after trimming trailing whitespace.
    """
    if ends_with_period(response):
        return (
            True,
            "The response ends with a period as required."
        )

    return (
        False,
        "The response must end with a period '.'. To fix this, ensure the final non-whitespace character is a period. "
        "If your Markdown ends with a code block or list, append a short concluding sentence after it (e.g., 'This concludes the analysis.')."
    )

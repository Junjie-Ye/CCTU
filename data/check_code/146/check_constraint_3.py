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
 If the agent intends to use the `historical_composer_info_retriever` tool, it must retrieve the symphony counts for the target composers. The solution must be completed within 2 to 6 total interaction turns, allowing for potential error correction while ensuring efficiency. The agent must make between 2 to 5 total tool calls across all interaction steps to balance thoroughness and efficiency. The final answer must be concise, with a maximum length of 150 characters. Additionally, the entire response must be formatted using Markdown syntax, including proper use of headings, bold/italic text, and code blocks to enhance readability and structure.

response_constraints_non_length:
- idx 3: ('Response', 'Format', "The agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, bold/italic text, and code blocks to enhance readability and structure.")
"""

import re
from typing import Tuple

# Helper regex patterns
FENCED_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
HEADING_LINE_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE)
BOLD_RE = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", re.DOTALL)
ITALIC_RE = re.compile(
    r"(?<!\*)\*(?=\S)(.+?)(?<=\S)\*(?!\*)|(?<!_)_(?=\S)(.+?)(?<=\S)_(?!_)",
    re.DOTALL,
)


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks from text."""
    return FENCED_BLOCK_RE.sub("", text)


def _has_balanced_fences(text: str) -> bool:
    """Check that triple backtick fences are balanced."""
    return text.count("```") % 2 == 0


def _has_code_block(text: str) -> bool:
    """Check presence of at least one fenced code block."""
    return bool(FENCED_BLOCK_RE.search(text))


def _has_heading_outside_code(text: str) -> bool:
    """Check presence of at least one Markdown heading outside code blocks."""
    no_code = _strip_code_blocks(text)
    return bool(HEADING_LINE_RE.search(no_code))


def _has_bold_or_italic_outside_code(text: str) -> Tuple[bool, str]:
    """Check presence of bold or italic formatting outside code blocks."""
    no_code = _strip_code_blocks(text)
    if BOLD_RE.search(no_code):
        return True, "bold"
    if ITALIC_RE.search(no_code):
        return True, "italic"
    return False, ""


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (# ...)
    - Bold or italic emphasis
    - A fenced code block (```)

    Additionally, if code fences are present, they must be balanced.
    Returns:
        (bool, str): validity flag and detailed English guidance.
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Include at least one Markdown element: heading, emphasis, or code block."
        )

    errors = []
    warnings = []
    found_elements = []

    # Check code fence balance (required if fences present)
    if not _has_balanced_fences(response):
        errors.append(
            "Code fences are unbalanced. Ensure triple backticks appear in matched pairs."
        )

    # Check for elements
    has_code_block = _has_code_block(response)
    has_heading = _has_heading_outside_code(response)
    has_emph, emph_kind = _has_bold_or_italic_outside_code(response)

    # OR logic: At least one element must be present
    has_any_element = has_code_block or has_heading or has_emph

    if not has_any_element:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. Emphasis - bold (**text**) or italic (*text*)\n"
            "3. A fenced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Record what was found
    if has_heading:
        found_elements.append("heading")
    else:
        warnings.append(
            "Consider adding a heading for structure (e.g., '# Title').")

    if has_emph:
        found_elements.append(f"{emph_kind or 'emphasis'}")
    else:
        warnings.append(
            "Consider adding emphasis (bold **text** or italic *text*).")

    if has_code_block:
        found_elements.append("code block")
    else:
        warnings.append(
            "Consider adding a code block for examples (```code```).")

    # Build response message
    if errors:
        # Has errors (like unbalanced fences) but still passes (OR logic)
        return (
            True,
            f"Format acceptable (with issues): Found {', '.join(found_elements)}. "
            f"Issues to fix: {' '.join(errors)}. "
            f"Suggestions: {' '.join(warnings) if warnings else 'None'}"
        )
    elif warnings:
        return (
            True,
            f"Format valid: Found {', '.join(found_elements)}. "
            f"Suggestions: {' '.join(warnings)}"
        )
    else:
        return (
            True,
            f"Format excellent: Found {', '.join(found_elements)}."
        )

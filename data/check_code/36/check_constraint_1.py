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
 Your response must be between 30 and 50 words in length to ensure clarity and conciseness, must provide the necessary data points and classification to determine normality, must be formatted using Markdown syntax with proper use of elements such as headings, bold/italic text, and lists to enhance readability and structure, and must utilize the 'bmi_calculator' tool no more than 2 times in total.

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'The response must be formatted using Markdown syntax, including appropriate use of headings, lists, bold/italic text, and code blocks to enhance readability and structure.')
"""

import re
from typing import Tuple

# Helper regex patterns compiled once for efficiency
RE_HEADING = re.compile(r'(?m)^\s{0,3}#{1,6}\s+\S')
RE_ULIST = re.compile(r'(?m)^\s{0,3}[-*+]\s+\S')
RE_OLIST = re.compile(r'(?m)^\s{0,3}\d+\.\s+\S')
RE_CODEBLOCK = re.compile(r'(?s)```+[\w-]*\n.*?\n```+')
# Bold: **text** or __text__ (avoid capturing whitespace-only content)
RE_BOLD = re.compile(r'(\*\*|__)(?=\S)(.+?)(?<=\S)\1', re.S)
# Italic: *text* or _text_ but not bold (avoid ** and __)
RE_ITALIC_STAR = re.compile(r'(?<!\*)\*(?=\S)(.+?)(?<=\S)\*(?!\*)', re.S)
RE_ITALIC_UNDERSCORE = re.compile(r'(?<!_)_(?=\S)(.+?)(?<=\S)_(?!_)', re.S)


def _strip_fenced_codeblocks(text: str) -> str:
    """Remove fenced code blocks (```...```) from text to avoid false positives when scanning for other markdown features."""
    return re.sub(RE_CODEBLOCK, '', text)


def _has_heading(text: str) -> bool:
    return bool(RE_HEADING.search(text))


def _has_list(text: str) -> bool:
    return bool(RE_ULIST.search(text) or RE_OLIST.search(text))


def _has_bold(text: str) -> bool:
    return bool(RE_BOLD.search(text))


def _has_italic(text: str) -> bool:
    return bool(RE_ITALIC_STAR.search(text) or RE_ITALIC_UNDERSCORE.search(text))


def _has_codeblock(text: str) -> bool:
    # Additionally ensure fence balance (even number of triple-backtick fences)
    fence_count = text.count("```")
    return fence_count >= 2 and fence_count % 2 == 0 and bool(RE_CODEBLOCK.search(text))


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - At least one heading (#, ##, ...).
    - At least one list (bulleted -, *, + or ordered 1.).
    - At least one bold segment (**text** or __text__).
    - At least one italic segment (*text* or _text_).
    - At least one fenced code block (``` ... ```), language label optional.

    Returns:
        (bool, str): A tuple where bool indicates pass/fail, and str provides detailed English guidance.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Response is empty or not a string. Provide a Markdown-formatted answer containing at least one formatting element."
        )

    text = response.strip()

    # Check presence of a fenced code block
    has_codeblock = _has_codeblock(text)

    # Remove code blocks before scanning for other features to avoid false positives
    non_code_text = _strip_fenced_codeblocks(text)

    # Check each Markdown element
    has_heading = _has_heading(non_code_text)
    has_list = _has_list(non_code_text)
    has_bold = _has_bold(non_code_text)
    has_italic = _has_italic(non_code_text)

    # OR logic: At least one element must be present
    has_any_markdown = has_heading or has_list or has_bold or has_italic or has_codeblock

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n"
            "- A heading (e.g., '# BMI Assessment')\n"
            "- A list (e.g., '- Healthy range' or '1. Normal weight')\n"
            "- Bold text (e.g., '**BMI**: 22.3')\n"
            "- Italic text (e.g., '*Classification*: Normal')\n"
            "- A fenced code block (```code```)\n\n"
            "Example minimal format: '**BMI**: 22.3' (just bold text is sufficient)"
        )

    # Optional: Provide feedback on what was found (suggestions for improvement)
    found_elements = []
    if has_heading:
        found_elements.append("heading")
    if has_list:
        found_elements.append("list")
    if has_bold:
        found_elements.append("bold text")
    if has_italic:
        found_elements.append("italic text")
    if has_codeblock:
        found_elements.append("code block")

    # Check for code block requirement if specifically mentioned
    if not has_codeblock:
        # Only mention this as a suggestion, not a requirement
        suggestion = " Consider adding a fenced code block (```) for better structure if appropriate."
    else:
        suggestion = ""

    return (
        True,
        f"Markdown format check passed: Found {', '.join(found_elements)}.{suggestion}"
    )

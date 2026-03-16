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
 Your answer must be derived by making between 1 and 2 total tool calls using the available tools. Ensure you only use the tools provided and do not rely on internal knowledge. The total number of interaction turns (including tool calls and responses) must not exceed 3. The final response must be formatted using Markdown syntax to enhance readability and structure, and must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period to ensure proper sentence closure.)')
- idx 3: ('Response', 'Format', "(Response, Format, Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.))")
"""

import re
from typing import Tuple, List

# Helper regex patterns for Markdown detection and validation
# Valid headings: "# Title"
HEADING_RE = re.compile(r'^(#{1,6})\s+\S', re.MULTILINE)
BAD_HEADING_SPACING_RE = re.compile(
    r'^(#{1,6})(\S)', re.MULTILINE)  # "#Title" (missing space)
BULLET_LIST_RE = re.compile(
    r'^[*-]\s+\S', re.MULTILINE)  # "- item" or "* item"
BAD_BULLET_SPACING_RE = re.compile(
    r'^([*-])(\S)', re.MULTILINE)  # "-item" (missing space)
NUMBERED_LIST_RE = re.compile(r'^\d+\.\s+\S', re.MULTILINE)  # "1. item"
BAD_NUMBERED_SPACING_RE = re.compile(
    r'^(\d+\.)(\S)', re.MULTILINE)  # "1.item" (missing space)
BOLD_RE = re.compile(r'\*\*[^*\n]+\*\*')  # **bold**
ITALIC_RE = re.compile(r'(?<!\*)\*[^*\n]+\*(?!\*)')  # *italic* (not bold)
LINK_RE = re.compile(r'\[[^\]]+\]\([^)]+\)')  # [text](url)
FENCE_RE = re.compile(r'```')  # code fence delimiter


def _has_balanced_fences(text: str) -> bool:
    """
    Check that fenced code blocks (```) are balanced.
    """
    return len(FENCE_RE.findall(text)) % 2 == 0


def _detect_markdown_elements(text: str) -> List[str]:
    """
    Return a list of detected Markdown structural elements.
    """
    elements = []
    if HEADING_RE.search(text):
        elements.append("heading")
    if BULLET_LIST_RE.search(text) or NUMBERED_LIST_RE.search(text):
        elements.append("list")
    if BOLD_RE.search(text):
        elements.append("bold")
    if ITALIC_RE.search(text):
        elements.append("italic")
    if LINK_RE.search(text):
        elements.append("link")
    # Code blocks: presence of matched fences is considered Markdown structure
    if FENCE_RE.search(text) and _has_balanced_fences(text):
        elements.append("fenced_code_block")
    return elements


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is formatted using Markdown syntax with proper structure.

    Checks performed:
    - At least one Markdown structural element is present (heading, list, bold/italic, link, or fenced code block).
    - Fenced code blocks (```) are balanced (opened and closed).
    - Common spacing errors are flagged (e.g., '#Title' should be '# Title', '-item' should be '- item', '1.item' should be '1. item').
    """
    if not response or not response.strip():
        return (
            False,
            "The response is empty. Provide a Markdown-formatted answer that includes at least one structural element such as a heading (# ...), a list (- item or 1. item), bold (**text**), italics (*text*), a link ([text](url)), or a fenced code block (```language ... ```)."
        )

    # Require at least one structural element to ensure the response leverages Markdown for readability
    elements = _detect_markdown_elements(response)
    if not elements:
        return (
            False,
            "The response lacks Markdown structure. Add at least one of the following: a heading (# Title), a list (- item or 1. item), bold (**text**), italics (*text*), a link ([text](https://example.com)), or a fenced code block (```language ... ```). Ensure the structure meaningfully organizes the content."
        )

    # Passed all checks
    return (
        True,
        "Pass: The response uses Markdown correctly (detected elements: {}). Maintain clear structure and balanced code fences.".format(
            ", ".join(elements))
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period as the last non-whitespace character.
    """
    if response is None:
        return (
            False,
            "The response is missing. Provide a complete Markdown-formatted answer and ensure the final non-whitespace character is a period '.'."
        )

    stripped = response.rstrip()
    if not stripped:
        return (
            False,
            "The response is empty. Provide a complete Markdown-formatted answer and ensure it ends with a period '.'."
        )

    if stripped.endswith('.'):
        return (
            True,
            "Pass: The response ends with a period. Ensure no extra characters appear after the final period."
        )

    # If the response ends with a code fence, explicitly instruct to add a concluding sentence after it
    if stripped.endswith("```"):
        return (
            False,
            "The response ends with a code fence (```). Add a brief concluding sentence after the closing fence that ends with a period '.'. For example: After the code block, add a line like 'This completes the result.'."
        )

    return (
        False,
        "The response must end with a period '.'. Add a concluding sentence or adjust the last sentence so that the final non-whitespace character is a period. Avoid trailing spaces or Markdown tokens after the period."
    )

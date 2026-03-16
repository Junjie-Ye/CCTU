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
 You must obtain the answer by making between 6 and 8 total tool calls, inclusive. Ensure all information is derived from tool calls and not internal knowledge. If a tool call fails, analyze the error and retry until success. The response must end with a period and be formatted using Markdown syntax with proper use of elements like headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', "(Response, Punctuation, Ending punctuation (Specifies that the agent's response must end with a period.))")
- idx 2: ('Response', 'Format', "(Response, Format, Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.))")
"""

import re
from typing import Tuple

# Helper regex patterns for Markdown feature detection
# # H1 .. ###### H6 at line start
HEADINGS_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S")
# unordered or ordered list item
LIST_RE = re.compile(r"(?m)^\s{0,3}(?:[-*+]\s+\S|\d+\.\s+\S)")
BOLD_RE = re.compile(r"\*\*(?=\S)(?:.*?\S)\*\*", re.S)  # **bold**
ITALIC_RE = re.compile(r"(?<!\*)\*(?=\S)(?:.*?\S)\*(?!\*)",
                       re.S)  # *italic* (avoid **)
LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")  # [text](url)
# fenced code block with optional language
CODEBLOCK_RE = re.compile(r"```[ \t]*[a-zA-Z0-9_-]*\n[\s\S]*?```", re.S)


def _has_heading(text: str) -> bool:
    return bool(HEADINGS_RE.search(text))


def _has_list(text: str) -> bool:
    return bool(LIST_RE.search(text))


def _has_emphasis(text: str) -> bool:
    return bool(BOLD_RE.search(text) or ITALIC_RE.search(text))


def _has_link(text: str) -> bool:
    return bool(LINK_RE.search(text))


def _has_fenced_codeblock(text: str) -> bool:
    return bool(CODEBLOCK_RE.search(text))


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' as the last non-whitespace character.
    """
    if response is None:
        return (
            False,
            "The response is empty. Provide a complete answer that ends with a single period '.' as the last non-whitespace character."
        )

    stripped = response.rstrip()
    if not stripped:
        return (
            False,
            "The response contains only whitespace. Provide content and ensure the last non-whitespace character is a period '.'."
        )

    last_char = stripped[-1]
    if last_char == ".":
        return (
            True,
            "Pass: The response ends with a period '.' as required."
        )

    return (
        False,
        "The response must end with a period '.'. Make the final non-whitespace character a single '.' (for example, add a short concluding sentence like 'This completes the analysis.' at the very end). "
        "Avoid trailing spaces after the period, and if your response currently ends with a code block or heading, add a concluding sentence after it that ends with a period."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - Headings
    - Lists (ordered or unordered)
    - Emphasis (bold or italic)
    - Links
    - Fenced code blocks
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. Provide an answer with at least one Markdown element: heading, list, emphasis, link, or code block."
        )

    has_heading = _has_heading(response)
    has_list = _has_list(response)
    has_emphasis = _has_emphasis(response)
    has_link = _has_link(response)
    has_codeblock = _has_fenced_codeblock(response)

    # OR logic: At least one element must be present
    has_any_markdown = has_heading or has_list or has_emphasis or has_link or has_codeblock

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. A list (e.g., '- Item' or '1. Step')\n"
            "3. Emphasis (e.g., **bold** or *italic*)\n"
            "4. A link (e.g., [example](https://example.com))\n"
            "5. A fenced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Build feedback on what was found and missing
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append(
            "- Add a heading for structure (e.g., '# Analysis').")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append(
            "- Add a list for organization (e.g., '- Key point').")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("- Use emphasis (e.g., **bold** or *italic*).")

    if has_link:
        found_elements.append("link")
    else:
        suggestions.append("- Add a link for reference (e.g., [source](url)).")

    if has_codeblock:
        found_elements.append("code block")
    else:
        suggestions.append("- Add a code block for examples (```code```).")

    # Build response message
    if suggestions:
        guidance = [
            f"Pass: The response includes {', '.join(found_elements)}.",
            "",
            "For improved formatting, consider adding:",
        ] + suggestions + [
            "",
            "Example complete structure:",
            "# Title",
            "- List item 1",
            "- **Bold** item 2",
            "[Link](https://example.com)",
            "```python",
            "# Code example",
            "```"
        ]
        return (True, "\n".join(guidance))
    else:
        return (
            True,
            f"Pass: The response includes {', '.join(found_elements)} and is properly formatted in Markdown."
        )

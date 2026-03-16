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
 You must use at most 8 tool calls to determine the answer, ensuring all information is obtained through the provided functions without relying on internal knowledge. Additionally, your final response must be formatted using Markdown syntax with proper headings, lists, bold/italic text, and code blocks to clearly present your findings and conclusion. Ensure your final sentence ends with a period to maintain proper sentence closure.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 2: ('Response', 'Punctuation', '(Response, Punctuation, ends with a period)')
"""

import re
from typing import Tuple

# Helper regex patterns compiled once
RE_HEADING = re.compile(r'(?m)^(?:\s{0,3})(#{1,6})\s+\S')
RE_BULLET_LIST = re.compile(r'(?m)^(?:\s{0,3})[-+*]\s+\S')
RE_ORDERED_LIST = re.compile(r'(?m)^(?:\s{0,3})\d+\.\s+\S')
RE_BOLD = re.compile(r'(\*\*[^*\n]+\*\*|__[^_\n]+__)')
# Italic but try to avoid matching bold
RE_ITALIC = re.compile(r'(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)')
RE_INLINE_CODE = re.compile(r'`[^`\n]+`')
RE_FENCE = re.compile(r'```')  # count occurrences to check balance


def _strip_trailing_whitespace(text: str) -> str:
    return re.sub(r'\s+\Z', '', text or '')


def _has_heading(text: str) -> bool:
    return bool(RE_HEADING.search(text or ''))


def _has_list(text: str) -> bool:
    return bool(RE_BULLET_LIST.search(text or '') or RE_ORDERED_LIST.search(text or ''))


def _has_emphasis(text: str) -> bool:
    t = text or ''
    return bool(RE_BOLD.search(t) or RE_ITALIC.search(t))


def _has_code(text: str) -> Tuple[bool, bool]:
    """
    Returns (has_any_code, fences_balanced_if_present)
    - has_any_code true if inline code or fenced block exists.
    - fences_balanced_if_present false only if at least one fence exists and the count is odd.
    """
    t = text or ''
    inline = bool(RE_INLINE_CODE.search(t))
    fence_count = len(RE_FENCE.findall(t))
    has_fenced = fence_count >= 2  # at least one open and one close
    fences_balanced = (fence_count % 2 == 0)
    has_any = inline or has_fenced
    # If there are no fences, consider fences balanced by default
    return has_any, (fences_balanced if fence_count > 0 else True)


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (#, ##, ...)
    - A list (bulleted or ordered)
    - Emphasis (bold **text** or italic *text*)
    - Code element (inline `code` or fenced code block ```...```)

    Additionally, if fenced code blocks are present, they must be properly balanced.
    """
    text = response or ''
    issues = []
    suggestions = []
    found_elements = []

    # Check each element
    has_heading = _has_heading(text)
    has_list = _has_list(text)
    has_emphasis = _has_emphasis(text)
    has_code, fences_balanced = _has_code(text)

    # OR logic: At least one element must be present
    has_any_element = has_heading or has_list or has_emphasis or has_code

    if not has_any_element:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Summary')\n"
            "2. A list (e.g., '- item' or '1. step')\n"
            "3. Emphasis (e.g., **bold** or *italic*)\n"
            "4. Code formatting (e.g., `inline code` or ```code block```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Record what was found
    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append("Consider adding a heading for structure.")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append("Consider adding a list for organization.")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("Consider using emphasis for key points.")

    if has_code:
        found_elements.append("code formatting")
    else:
        suggestions.append("Consider adding code formatting for examples.")

    # Check code fence balance (required if fences are present)
    if not fences_balanced:
        issues.append(
            "Balance fenced code blocks: every opening '```' must have a matching closing '```'."
        )

    # Build response message
    if issues:
        # Has issues (like unbalanced fences) but still passes (OR logic)
        return (
            True,
            f"Format acceptable (with issues): Found {', '.join(found_elements)}. "
            f"Issues to fix: {' '.join(issues)}. "
            f"Suggestions: {' '.join(suggestions) if suggestions else 'None'}"
        )
    elif suggestions:
        return (
            True,
            f"Format valid: Found {', '.join(found_elements)}. "
            f"Suggestions: {' '.join(suggestions)}"
        )
    else:
        return (
            True,
            f"Format excellent: Found {', '.join(found_elements)}."
        )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final sentence ends with a period '.' exactly at the end of the response
    (ignoring trailing whitespace). If the response ends with a code fence or any other character,
    instruct to add a concluding sentence that ends with a period.
    """
    trimmed = _strip_trailing_whitespace(response or '')
    if not trimmed:
        return False, (
            "The response is empty. Provide a Markdown-formatted answer and end the final sentence with a period '.'."
        )

    if trimmed.endswith('.'):
        return True, "The response ends with a period, satisfying the punctuation requirement."

    # Special hint if it ends with a closing code fence
    if trimmed.endswith('```'):
        return False, (
            "The response ends with a closing code fence '```' rather than a period. "
            "Add a short concluding sentence after the code block that ends with a period (e.g., 'This completes the task.')."
        )

    return False, (
        "Ensure the final sentence ends with a period '.'. Place the period as the last character of the response "
        "after trimming any trailing whitespace, and avoid adding extra content after it."
    )

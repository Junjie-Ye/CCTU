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
 The answer must be formatted using Markdown syntax, including elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure. Additionally, the response must be between 300 and 500 words in length to ensure sufficient detail while maintaining conciseness. If the agent intends to invoke the `academic_relationship_finder`, the `literary_connection_finder` must strictly be executed beforehand. The `literary_connection_finder` must not be invoked more than two times during this task.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must be formatted using Markdown syntax, including elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.')
"""

import re
from typing import Tuple

# Helper regex patterns for Markdown elements
HEADING_ATX_RE = re.compile(r'^(#{1,6})\s+\S', re.MULTILINE)
HEADING_SETEXT_RE = re.compile(r'^[^\n]+\n[=-]{3,}\s*$', re.MULTILINE)

LIST_RE = re.compile(r'^(?:\s{0,3})(?:[-+*]|\d{1,3}\.)\s+\S', re.MULTILINE)

BOLD_RE = re.compile(r'(\*\*[^*\n][^*]*?\*\*|__[^_\n][^_]*?__)')
ITALIC_RE = re.compile(
    r'(?<!\*)\*[^*\n][^*]*?\*(?!\*)|(?<!_)_[^_\n][^_]*?_(?!_)')
BOLD_ITALIC_COMBINED_RE = re.compile(
    r'(\*\*\*[^*\n][^*]*?\*\*\*|___[^_\n][^_]*?___)')

LINK_RE = re.compile(r'\[[^\]]+]\((https?://[^)\s]+)\)')

# Code block: optional language, content, closing fence
CODEBLOCK_RE = re.compile(r'```[a-zA-Z0-9_-]*\n([\s\S]*?)\n?```')

FENCE_RE = re.compile(r'```')


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks to avoid false positives when checking other Markdown elements."""
    return re.sub(r'```[\s\S]*?```', '', text)


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading
    - A list (bulleted or numbered)
    - Bold and italic emphasis (or combined bold-italic)
    - A hyperlink in [text](https://...) form
    - A fenced code block (```) with non-empty content

    Also checks that fenced code blocks are balanced.
    Returns:
        (bool, str): pass/fail and detailed guidance in English.
    """
    if not isinstance(response, str) or not response.strip():
        return (False, "The response is empty. Provide a Markdown-formatted answer with at least one formatting element: heading, list, bold/italic, link, or code block.")

    # Balance check for code fences - still required for code blocks
    fences = len(FENCE_RE.findall(response))
    fences_balanced = (fences % 2 == 0)

    # Code block presence with non-whitespace content
    codeblock_matches = CODEBLOCK_RE.findall(response)
    has_codeblock_with_content = any(bool(m.strip())
                                     for m in codeblock_matches)

    # Check other elements outside code blocks to ensure they are actual Markdown, not code
    visible = _strip_code_blocks(response)

    has_heading = bool(HEADING_ATX_RE.search(visible)
                       or HEADING_SETEXT_RE.search(visible))
    has_list = bool(LIST_RE.search(visible))

    # Emphasis: allow either explicit bold+italic separately, or a combined bold-italic token
    has_bold = bool(BOLD_RE.search(visible))
    has_italic = bool(ITALIC_RE.search(visible))
    has_bold_italic_combined = bool(BOLD_ITALIC_COMBINED_RE.search(visible))
    has_bold_and_italic = (has_bold and has_italic) or has_bold_italic_combined

    has_link = bool(LINK_RE.search(visible))

    # OR logic: At least one element must be present
    elements_present = [has_heading, has_list,
                        has_bold_and_italic, has_link, has_codeblock_with_content]
    has_any_markdown = any(elements_present)

    if not has_any_markdown:
        return (False,
                "The response lacks Markdown formatting. Include at least ONE of these elements:\n\n"
                "Options:\n"
                "1. A heading (e.g., '# Title' or 'Title' followed by '===')\n"
                "2. A bulleted or numbered list (e.g., '- item' or '1. item')\n"
                "3. Bold AND italic emphasis (e.g., '**bold**' and '*italic*', or '***bold-italic***')\n"
                "4. A Markdown link like [example](https://example.com)\n"
                "5. A fenced code block with content:\n"
                "   ```python\n"
                "   # your code here\n"
                "   ```\n\n"
                "Example minimal format: '# Summary' (just a heading is sufficient)")

    # Collect information about what was found
    found_elements = []
    suggestions = []
    issues = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append("Consider adding a heading for structure.")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append("Consider adding a list for organization.")

    if has_bold_and_italic:
        found_elements.append("bold/italic emphasis")
    else:
        suggestions.append(
            "Consider adding bold and italic text for emphasis.")

    if has_link:
        found_elements.append("hyperlink")
    else:
        suggestions.append("Consider adding a link for reference.")

    if has_codeblock_with_content:
        found_elements.append("code block")
        if not fences_balanced:
            issues.append(
                "Fix unbalanced code fences: the number of opening and closing ``` fences must match.")
    else:
        suggestions.append("Consider adding a code block for examples.")

    if not fences_balanced and fences > 0:
        issues.append(
            "Fix unbalanced code fences: the number of opening and closing ``` fences must match.")

    # Build result message
    if issues:
        # Has some issues but still passes (OR logic)
        return (True,
                f"Pass (with notes): Found {', '.join(found_elements)}. "
                f"Issues to address: {' '.join(issues)}. "
                f"Suggestions: {' '.join(suggestions) if suggestions else 'None'}.")
    else:
        return (True,
                f"Pass: Found {', '.join(found_elements)}. "
                f"Suggestions: {' '.join(suggestions) if suggestions else 'None'}.")

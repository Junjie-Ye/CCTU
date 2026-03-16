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
 The solution must be derived through tool calls, the entire reasoning process must be completed within at most 10 interaction turns, the final answer must end with a period to ensure proper sentence closure, the response must contain at least 300 words to ensure sufficient detail in explaining the multi-step reasoning process, and the entire response must be formatted using Markdown syntax (e.g., with headings, lists, and bold/italic text) to enhance readability and structure.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'Ending punctuation (.)')
- idx 3: ('Response', 'Format', '(Response, Format, "Markdown (Mandates that the agent\'s entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")')
"""

import re
from typing import Tuple, Optional

# ----------------------------
# Helper regex patterns
# ----------------------------
HEADING_LINE_RE = re.compile(
    r'(?m)^\s{0,3}#{1,6}\s+\S')  # Markdown ATX headings
# Bulleted or numbered list
LIST_LINE_RE = re.compile(r'(?m)^\s{0,3}(?:[-*+]\s+\S|\d+\.\s+\S)')
EMPHASIS_RE = re.compile(
    r'(\*\*[^*\n]+?\*\*|\*[^*\n]+?\*|__[^_\n]+?__|_[^_\n]+?_)'
)  # bold/italic emphasis (simple heuristic)


# ----------------------------
# Utility helpers
# ----------------------------
def _first_nonempty_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.strip():
            return line
    return None


def _starts_with_markdown_heading(text: str) -> bool:
    first = _first_nonempty_line(text or "")
    if first is None:
        return False
    return bool(re.match(r'^\s{0,3}#{1,6}\s+\S', first))


def _has_markdown_heading(text: str) -> bool:
    return bool(HEADING_LINE_RE.search(text or ""))


def _has_markdown_list(text: str) -> bool:
    return bool(LIST_LINE_RE.search(text or ""))


def _has_emphasis(text: str) -> bool:
    return bool(EMPHASIS_RE.search(text or ""))


def _code_fences_balanced(text: str) -> Tuple[bool, str]:
    """
    Validate that triple backtick code fences (```) are balanced.
    We do not require code blocks to exist, but if present, they must be matched.
    """
    fence_count = text.count("```")
    if fence_count % 2 != 0:
        return (
            False,
            "Detected an unmatched fenced code block (```); ensure every opening fence has a closing fence and that fenced blocks are not cut off at the end.",
        )
    return True, "Code fences are balanced or absent."


def _last_non_ws_char(text: str) -> Optional[str]:
    if text is None:
        return None
    stripped = text.rstrip()
    if not stripped:
        return None
    return stripped[-1]


# ----------------------------
# Validators
# ----------------------------
def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final non-whitespace character is a period '.'.

    Returns:
        (is_valid, message)
        - is_valid: True if the response ends with '.', False otherwise.
        - message: Detailed, actionable English guidance.
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. End the final sentence with a period '.' as the last non-whitespace character.",
        )

    stripped = response.rstrip()
    last_char = stripped[-1]

    if last_char == ".":
        return (
            True,
            "Pass: The response ends with a period '.' as required.",
        )

    if stripped.endswith("```"):
        return (
            False,
            "Your response ends with a fenced code block (```), but the requirement is that the entire response must end with a period. Add a concluding Markdown sentence after the code block, for example: 'This concludes the analysis.'.",
        )

    return (
        False,
        f"Your response currently ends with '{last_char}'. The final non-whitespace character must be a period '.'. Replace the last punctuation or append a concluding sentence that ends with a period.",
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - Starts with a Markdown heading (e.g., '# Title' or '## Analysis')
    - Includes at least one Markdown list (bulleted '-'/'*' or numbered '1.')
    - Uses at least one emphasis token (bold **text** or italic *text*)
    - If fenced code blocks are present, their backticks must be balanced.

    Returns:
        (is_valid, message)
        - is_valid: True if at least one formatting element is present.
        - message: Detailed, actionable English guidance.
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. Provide an answer with at least one formatting element: heading, list, or emphasis.",
        )

    issues = []
    suggestions = []
    found_elements = []

    # Check for each element
    starts_with_heading = _starts_with_markdown_heading(response)
    has_list = _has_markdown_list(response)
    has_emphasis = _has_emphasis(response)

    # Check code fence balance (only if fences are present)
    fences_ok, fences_msg = _code_fences_balanced(response)
    has_fences = "```" in response

    # OR logic: At least one of the main elements must be present
    has_any_formatting = starts_with_heading or has_list or has_emphasis

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "1. Start with a heading (e.g., '# Title' or '## Analysis')\n"
            "2. Add a list (e.g., '- Item 1' or '1. Step one')\n"
            "3. Use emphasis (e.g., **bold** or *italic*)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Record what was found
    if starts_with_heading:
        found_elements.append("starts with heading")
    else:
        suggestions.append(
            "Consider starting with a heading for better structure.")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append("Consider adding a list for organization.")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("Consider using bold or italic for emphasis.")

    # Handle code fence issues (not blocking, but noted)
    if has_fences and not fences_ok:
        issues.append(fences_msg)

    # Build response message
    if issues:
        return (
            True,  # Still passes with OR logic
            f"Format acceptable: Found {', '.join(found_elements)}. "
            f"Issues to address: {' '.join(issues)}. "
            f"Suggestions: {' '.join(suggestions) if suggestions else 'None'}"
        )
    elif suggestions:
        return (
            True,
            f"Format acceptable: Found {', '.join(found_elements)}. "
            f"Suggestions for improvement: {' '.join(suggestions)}"
        )
    else:
        return (
            True,
            f"Format excellent: Found {', '.join(found_elements)}."
        )

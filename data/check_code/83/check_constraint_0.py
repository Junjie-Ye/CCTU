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
 The answer must end with a period to ensure proper sentence closure. Additionally, the solution must use **at most 15 total tool calls** across all interaction steps to ensure efficiency and avoid excessive iterations. The final answer must be formatted using Markdown syntax, including proper use of headings (e.g., ### Section), bullet points, bold text (**bold**), and line breaks for readability. All factual claims must be presented in plain text without formatting, while organizational elements must follow Markdown conventions.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', "(Main Category, Ending punctuation, The agent's response must end with a period to ensure proper sentence closure.)")
- idx 2: ('Response', 'Format', 'The final answer must be formatted using Markdown syntax, including proper use of headings (e.g., ### Section), bullet points, bold text (**bold**), and line breaks for readability. All factual claims must be presented in plain text without formatting, while organizational elements must follow Markdown conventions.')
"""

import re
from typing import Tuple, List

# ------------------------------
# Helper utilities
# ------------------------------

HEADING_RE = re.compile(r'^\s{0,3}#{1,6}\s+\S', re.MULTILINE)
BULLET_RE = re.compile(r'^\s{0,3}[-*+]\s+\S', re.MULTILINE)
BOLD_RE = re.compile(r'\*\*(.+?)\*\*', re.DOTALL)
INLINE_CODE_RE = re.compile(r'`[^`]+`', re.DOTALL)
FENCED_CODE_RE = re.compile(r'```[\s\S]*?```', re.MULTILINE)


def _last_non_whitespace_char(text: str) -> str:
    i = len(text) - 1
    while i >= 0 and text[i].isspace():
        i -= 1
    return text[i] if i >= 0 else ''


def _has_blank_line(text: str) -> bool:
    return bool(re.search(r'\n\s*\n', text))


def _find_headings(text: str) -> List[str]:
    return HEADING_RE.findall(text)


def _find_bullets(text: str) -> List[str]:
    return BULLET_RE.findall(text)


def _find_bold_segments(text: str) -> List[str]:
    return [m.group(1) for m in BOLD_RE.finditer(text)]


def _looks_like_factual_claim(text: str) -> bool:
    """
    Heuristic: consider a bold segment as a factual claim if:
    - It contains digits; or
    - It has more than 6 words; or
    - It contains sentence punctuation suggesting a statement.
    """
    word_count = len(re.findall(r'\b\w+\b', text))
    has_digits = any(ch.isdigit() for ch in text)
    has_sentence_punct = bool(re.search(r'[.:;?!]', text))
    return has_digits or word_count > 6 or has_sentence_punct

# ------------------------------
# Validators
# ------------------------------


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period.
    """
    last_char = _last_non_whitespace_char(response)
    if last_char == '.':
        return True, "Valid: The response ends with a period as required."
    guidance = (
        "Invalid: The response must end with a single period.\n"
        "- Ensure the final non-whitespace character of the entire answer is '.'.\n"
        "- Do not place additional characters after the period (except whitespace).\n"
        f"- Current last non-whitespace character detected: '{last_char}' (empty means the response is blank).\n"
        "Fix: Append a '.' at the very end of the final line of your answer."
    )
    return False, guidance


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (e.g., ### Section)
    - Bullet points (lines starting with -, *, or + followed by a space)
    - Bold emphasis using **bold** for organizational labels
    - Line breaks for readability (multiple lines and at least one blank line recommended)
    - All factual claims must be in plain text
    - Organizational elements (headings, bullets, bold labels) should follow Markdown
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Provide an answer with at least one Markdown element: heading, bullet list, or bold labels."
        )

    issues: List[str] = []
    suggestions: List[str] = []
    found_elements: List[str] = []

    # 1) Check for at least one Markdown heading
    has_heading = HEADING_RE.search(response) is not None
    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append(
            "Consider adding a heading (e.g., '### Section') for organization.")

    # 2) Check for at least one bullet list item
    has_bullets = BULLET_RE.search(response) is not None
    if has_bullets:
        found_elements.append("bullet list")
    else:
        suggestions.append(
            "Consider adding bullet points (e.g., '- Item') for lists.")

    # 3) Check for at least one bold segment for organizational labels
    bold_segments = _find_bold_segments(response)
    has_bold = len(bold_segments) > 0
    if has_bold:
        found_elements.append("bold labels")
    else:
        suggestions.append(
            "Consider using **bold** for labels (e.g., **Summary**).")

    # OR logic: At least one Markdown element must be present
    has_any_markdown = has_heading or has_bullets or has_bold

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '### Section' or '# Title')\n"
            "2. Bullet points (e.g., '- Step 1' or '* Item')\n"
            "3. Bold labels (e.g., **Summary** or **Key Points**)\n\n"
            "Example minimal format: '### Summary' (just a heading is sufficient)"
        )

    # Check for readability (multiple lines)
    line_count = response.count('\n') + 1
    if line_count < 2:
        suggestions.append(
            "Consider using multiple lines for better readability.")

    # Check for blank lines between sections
    if '\n\n' not in response:
        suggestions.append(
            "Consider adding blank lines between sections for structure.")

    # Build response message
    success_msg = f"Valid: Found {', '.join(found_elements)}."

    if suggestions:
        success_msg += " Suggestions: " + " ".join(suggestions)

    return True, success_msg

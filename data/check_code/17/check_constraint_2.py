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
 Your answer must use between 18 and 20 words, involve at least 1 but no more than 3 total tool calls to external functions, be formatted using Markdown syntax with proper use of elements like headings, bold/italic text, and lists, and explicitly include the wind speed value in bold using Markdown (e.g., **165 mph**).

response_constraints_non_length:
- idx 2: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 3: ('Response', 'Identifiers', '(Response, Delimiting identifier, "Must include the wind speed value in bold using Markdown syntax (e.g., **165 mph**)")')
"""

import re
from typing import Tuple, List

# ----------------------------
# Helper utilities
# ----------------------------

FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def strip_code_segments(text: str) -> str:
    """
    Remove fenced and inline code segments from text to avoid false positives
    when validating Markdown constructs.
    """
    without_fenced = FENCED_BLOCK_RE.sub("", text)
    without_inline = INLINE_CODE_RE.sub("", without_fenced)
    return without_inline


def first_nonempty_line(lines: List[str]) -> int:
    """Return index of the first non-empty line or -1 if none."""
    for i, line in enumerate(lines):
        if line.strip():
            return i
    return -1


def has_markdown_heading(text: str) -> bool:
    """
    Detect at least one Markdown ATX heading (e.g., '# Title', '## Section').
    Requires a space after the hashes.
    """
    for line in text.splitlines():
        if re.match(r"^\s{0,3}#{1,6}\s+\S", line):
            return True
    return False


def first_line_is_heading(text: str) -> bool:
    """
    Ensure the first non-empty line is a Markdown heading to satisfy
    "formatted using Markdown with proper structure".
    """
    lines = text.splitlines()
    idx = first_nonempty_line(lines)
    if idx == -1:
        return False
    return bool(re.match(r"^\s{0,3}#{1,6}\s+\S", lines[idx]))


def has_markdown_list(text: str) -> bool:
    """
    Detect the presence of a Markdown list item:
    - unordered: -, *, + followed by space
    - ordered: 1. or 1) followed by space
    """
    pat = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)\S", re.MULTILINE)
    return bool(pat.search(text))


def has_emphasis(text: str) -> bool:
    """
    Detect presence of bold or italic emphasis.
    Bold: **text** or __text__
    Italic: *text* or _text_
    Avoid matching list bullets by requiring closing markers.
    """
    text_nc = strip_code_segments(text)

    bold_patterns = [
        re.compile(r"(?<!\*)\*\*(?=\S)(.+?)(?<=\S)\*\*(?!\*)", re.DOTALL),
        re.compile(r"(?<!_)__(?=\S)(.+?)(?<=\S)__(?!_)", re.DOTALL),
    ]
    italic_patterns = [
        re.compile(r"(?<!\*)\*(?!\*)(?=\S)(.+?)(?<=\S)\*(?!\*)", re.DOTALL),
        re.compile(r"(?<!_)_(?!_)(?=\S)(.+?)(?<=\S)_(?!_)", re.DOTALL),
    ]

    for p in bold_patterns + italic_patterns:
        if p.search(text_nc):
            return True
    return False


def has_balanced_emphasis_markers(text: str) -> bool:
    """
    Basic sanity check: counts of '**' and '__' should be even (outside code).
    This is a heuristic to catch obvious unbalanced emphasis.
    """
    s = strip_code_segments(text)
    return (s.count("**") % 2 == 0) and (s.count("__") % 2 == 0)


def find_bold_wind_speed(text: str) -> List[str]:
    """
    Find bold wind speed tokens like **165 mph** (also accept km/h, kph, kt, kts, knots, m/s).
    Returns list of matched tokens (without the surrounding **).
    """
    s = strip_code_segments(text)
    pattern = re.compile(
        r"\*\*\s*(\d+(?:\.\d+)?)\s*(mph|km\/h|kph|kt|kts|knots|m\/s)\s*\*\*",
        re.IGNORECASE,
    )
    return [m.group(0) for m in pattern.finditer(s)]


# ----------------------------
# Validators
# ----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least one of these Markdown elements:
    - A heading (preferably as the first non-empty line)
    - At least one list (bulleted or numbered)
    - At least one emphasis (bold or italic)
    No obviously unbalanced emphasis markers still required.
    """
    if not response or not response.strip():
        return (
            False,
            "Response is empty. Provide a Markdown-formatted answer with at least one of: heading, list, or emphasis."
        )

    # 检查是否有不平衡的标记（这是安全要求，必须满足）
    if not has_balanced_emphasis_markers(response):
        return (
            False,
            "Unbalanced emphasis markers detected. Ensure '**' and '__' appear in pairs outside code blocks."
        )

    # 检查是否至少有一个Markdown元素存在
    has_heading = has_markdown_heading(response)
    has_list = has_markdown_list(response)
    has_emp = has_emphasis(response)

    # 使用OR逻辑：至少一个为True
    has_any_formatting = has_heading or has_list or has_emp

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least one of: "
            "1. A Markdown heading (e.g., '# Title' or '## Section'), OR "
            "2. A bulleted or numbered list (e.g., '- item' or '1. item'), OR "
            "3. Bold or italic text (e.g., '**key value**' or '*important note*')."
        )

    # 可选的建议（不是错误）
    suggestions = []
    if has_heading and not first_line_is_heading(response):
        suggestions.append(
            "Consider placing a heading at the top (first non-empty line) for better structure."
        )

    suggestion_text = " " + " ".join(suggestions) if suggestions else ""

    return (
        True,
        f"Markdown format validated: Found at least one formatting element."
        f"{suggestion_text}"
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the wind speed value in bold using Markdown,
    for example: **165 mph**. Accepts common units: mph, km/h (kph), kt/kts/knots, m/s.
    """
    matches = find_bold_wind_speed(response)

    if not matches:
        return (
            False,
            "Missing bold wind speed value. Include a bold token like '**165 mph**' within the content, "
            "preferably in a list item. Use 'mph' if known; 'km/h', 'kt', 'kts', 'knots', or 'm/s' are also accepted."
        )

    return (
        True,
        "Bold wind speed value detected: " +
        ", ".join(matches) +
        ". Ensure it reflects the correct value from tools."
    )

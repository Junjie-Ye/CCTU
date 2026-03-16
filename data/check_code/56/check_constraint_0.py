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
 The answer must be formatted in Markdown syntax with proper use of headings, lists, bold/italic text, and code blocks to enhance readability. The answer must end with a period to ensure proper sentence closure. The agent may take no more than 8 interaction turns to arrive at the final answer.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', '(Response, Punctuation, "Ending punctuation (The agent\'s final answer must end with a period to ensure proper sentence closure.)")')
- idx 1: ('Response', 'Format', '(Response, Format, "Markdown (The agent\'s entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")')
"""

import re
from typing import List, Tuple


# ---------------------------
# Helper utilities (shared)
# ---------------------------

def _split_code_blocks(text: str) -> List[Tuple[str, bool]]:
    """
    Split text into segments, marking each as code or non-code based on fenced blocks (```).
    Each tuple is (segment_text, is_code).
    If code fences are unbalanced, the last segment will have is_code=True.
    """
    lines = text.splitlines(keepends=True)
    segments: List[Tuple[str, bool]] = []
    buf: List[str] = []
    in_code = False

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            if not in_code:
                # Flush previous non-code
                if buf:
                    segments.append(("".join(buf), False))
                    buf = []
                in_code = True
                buf.append(line)  # include opening fence in code segment
            else:
                # Closing fence ends code segment
                buf.append(line)
                segments.append(("".join(buf), True))
                buf = []
                in_code = False
        else:
            buf.append(line)

    if buf:
        segments.append(("".join(buf), in_code))
    return segments


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line
    return ""


def _non_code_text(segments: List[Tuple[str, bool]]) -> str:
    return "".join(seg for seg, is_code in segments if not is_code)


def _has_markdown_heading(non_code: str) -> bool:
    # Heading via #, ##, ... or underline style (=== or --- after a line)
    for i, line in enumerate(non_code.splitlines()):
        if re.match(r'^\s*#{1,6}\s+\S', line):
            return True
    # Underline style check
    lines = non_code.splitlines()
    for i in range(len(lines) - 1):
        if lines[i].strip() and re.match(r'^\s*(=+|-+)\s*$', lines[i + 1]):
            return True
    return False


def _first_nonempty_is_heading(non_code: str) -> bool:
    line = _first_nonempty_line(non_code)
    return bool(re.match(r'^\s*#{1,6}\s+\S', line) or
                (line and re.match(r'^\s*(=+|-+)\s*$', line) is not None))


def _has_list(non_code: str) -> bool:
    for line in non_code.splitlines():
        if re.match(r'^\s*([-*+])\s+\S', line):
            return True
        if re.match(r'^\s*\d+\.\s+\S', line):
            return True
    return False


def _has_emphasis(non_code: str) -> bool:
    # Bold: **text** or __text__
    if re.search(r'(\*\*[^*\n]+?\*\*|__[^_\n]+?__)', non_code):
        return True
    # Italic: *text* or _text_ but not bold
    if re.search(r'(?<!\*)\*[^*\n]+?\*(?!\*)|(?<!_)_[^_\n]+?_(?!_)', non_code):
        return True
    return False


def _count_code_blocks(segments: List[Tuple[str, bool]]) -> int:
    return sum(1 for _, is_code in segments if is_code)


def _code_fences_balanced(segments: List[Tuple[str, bool]]) -> bool:
    # If the final segment is code => unbalanced fences
    return not segments or not segments[-1][1]


# ---------------------------
# Validators (required)
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (preferably as the first non-empty line)
    - At least one list (bulleted or numbered)
    - Bold and/or italic emphasis
    - At least one fenced code block (```) with balanced fences
    """
    if not response or not response.strip():
        return (
            False,
            "Response is empty. Include at least one Markdown element: heading, list, emphasis, or code block."
        )

    segments = _split_code_blocks(response)
    non_code = _non_code_text(segments)

    # Check for each element
    has_heading = _has_markdown_heading(non_code)
    has_list = _has_list(non_code)
    has_emphasis = _has_emphasis(non_code)
    code_blocks = _count_code_blocks(segments)
    has_code_block = code_blocks >= 1
    fences_balanced = _code_fences_balanced(segments)

    # OR logic: at least one element must be present
    has_any_markdown = has_heading or has_list or has_emphasis or has_code_block

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n"
            "- A heading (e.g., '# Title' or '## Section')\n"
            "- A bulleted or numbered list (e.g., '- item' or '1. step')\n"
            "- Bold or italic emphasis (e.g., **important** or *note*)\n"
            "- A fenced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Collect information about what was found
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
        # Check if heading is first (suggestion only)
        if not _first_nonempty_is_heading(non_code):
            suggestions.append(
                "Consider placing a heading at the top for better structure.")

    if has_list:
        found_elements.append("list")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("Consider adding bold or italic text for emphasis.")

    if has_code_block:
        found_elements.append("code block")
        if not fences_balanced:
            suggestions.append(
                "Fix unbalanced code fences: ensure every ``` has a matching closing ```.")
    else:
        suggestions.append(
            "Consider adding a code block for structured examples.")

    # Build success message
    success_msg = f"OK: Found {', '.join(found_elements)}."

    if suggestions:
        success_msg += " Suggestions: " + " ".join(suggestions)

    return True, success_msg


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period ('.').
    If the response ends with a code block or any other character, instruct to add a concluding sentence with a final '.'.
    """
    stripped = response.rstrip()

    if stripped.endswith("."):
        return True, "Punctuation is compliant: the response ends with a period."

    # Check if the response ends with a code block fence
    segments = _split_code_blocks(response)
    ends_with_code_block = False
    if segments:
        last_seg_text, last_is_code = segments[-1]
        # Ends with a closed code block if the last segment is code and fences are balanced
        ends_with_code_block = last_is_code and _code_fences_balanced(
            segments) and stripped.endswith("```")

    if ends_with_code_block:
        return (
            False,
            "Your response ends with a code block and not with a sentence. Add a short concluding line after the code block that ends with a period, e.g.,\n"
            "This concludes the solution."
        )

    return (
        False,
        "The final character of your response must be a period ('.'). Ensure the last non-whitespace character is '.'. "
        "If the last line ends with another punctuation mark or closing quote/parenthesis, add a final '.' at the very end."
    )

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
 Your answer must end with a period to ensure proper sentence closure, must be formatted using Markdown syntax (including elements like headings, lists, code blocks, or bold/italic text) to enhance clarity and structure, must be obtained through no more than 5 total interaction turns with the tools, and must include the delimiter "Answer:" immediately before the boxed date to clearly separate the final result from preceding text.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'Ending punctuation (.)')
- idx 1: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 3: ('Response', 'Identifiers', "Include the delimiter 'Answer:' immediately before the boxed date to clearly separate the final result from preceding text.")
"""

import re
from typing import Tuple

# Helper regexes compiled once for reuse
RE_HEADING = re.compile(r'(?m)^\s{0,3}#{1,6}\s+\S')
RE_LIST = re.compile(r'(?m)^\s{0,3}(?:-|\*|\+|\d+\.)\s+\S')
RE_BOLD = re.compile(r'\*\*[^*\n][^*\n]*\*\*')
RE_ITALIC = re.compile(
    r'(?<!\*)\*[^*\n][^*\n]*\*(?!\*)|_(?!_)[^_\n][^_\n]*_(?!_)')
RE_LINK = re.compile(r'\[[^\]]+\]\([^)]+\)')
RE_FENCE = re.compile(r'```')
# "Answer:" delimiter immediately followed (optionally after spaces) by a bracketed token (boxed date)
RE_ANSWER_LINE = re.compile(
    r'(?mi)^\s*(?:\*\*)?Answer:(?:\*\*)?\s*\[[^\]]+\]\s*$')
RE_ANSWER_TOKEN = re.compile(r'Answer:')


def _last_visible_char(s: str) -> str:
    """Return the last non-whitespace character of the response, ignoring trailing spaces and newlines."""
    i = len(s) - 1
    while i >= 0 and s[i].isspace():
        i -= 1
    return s[i] if i >= 0 else ''


def _has_markdown_elements(s: str) -> Tuple[bool, str]:
    """Check presence of common Markdown elements and return a debug string listing what was found."""
    found = []
    if RE_HEADING.search(s):
        found.append("heading (# ...)")
    if RE_LIST.search(s):
        found.append("list (-, *, +, or numbered)")
    if RE_FENCE.search(s):
        found.append("fenced code block (```)")
    if RE_BOLD.search(s):
        found.append("bold (**...**)")
    if RE_ITALIC.search(s):
        found.append("italic (*...* or _..._)")
    if RE_LINK.search(s):
        found.append("link [text](url)")
    return (len(found) > 0, ", ".join(found))


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period ('.').
    - The last visible character (ignoring trailing whitespace) must be a period.
    """
    last = _last_visible_char(response)
    if last == '.':
        return True, "Pass: The response ends with a period. No changes needed."
    # If the response ends with a code fence or other punctuation, provide targeted guidance.
    if last == '`' and RE_FENCE.search(response):
        return False, (
            "Fail: Your response must end with a period ('.'). Currently it appears to end with a code fence. "
            "Add a concluding sentence after the closing ``` fence and ensure the very last visible character "
            "of the entire message is a period."
        )
    return False, (
        "Fail: Your response must end with a period ('.'). Ensure the final visible character of the whole "
        "message (after any code blocks or lists) is a period. For example, add a closing sentence like "
        "\"This completes the timeline.\"."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the entire response uses Markdown formatting appropriately.
    Heuristics applied:
      - At least one recognizable Markdown element should be present (heading, list, fenced code block, bold/italic, or link).
      - Fenced code blocks (```) must be balanced (even number of ``` markers).
    """
    has_md, found = _has_markdown_elements(response)
    # Check code fence balance
    fence_count = len(RE_FENCE.findall(response))
    fences_balanced = (fence_count % 2 == 0)

    if not has_md and fences_balanced:
        return False, (
            "Fail: The response is not sufficiently formatted in Markdown. Include at least one Markdown element, "
            "such as a heading (e.g., '# Title'), a list ('- item' or '1. item'), a fenced code block (```), "
            "bold (**text**), italic (*text*), or a link ([text](https://example.com))."
        )
    if not fences_balanced:
        return False, (
            f"Fail: Unbalanced fenced code blocks detected. Found {fence_count} occurrences of ``` "
            "which must be an even number. Ensure every opening ``` has a corresponding closing ```."
        )
    return True, (
        f"Pass: Markdown formatting detected ({found}). Code fences are balanced. No changes needed."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the delimiter 'Answer:' immediately before a boxed date on the same line.
    Accepted patterns include optional bolding, e.g., '**Answer:** [Date]'.
    Requirements:
      - The exact token 'Answer:' must be present.
      - On at least one line, 'Answer:' must be followed (optionally after spaces) by a bracketed token, e.g., [Date].
    """
    # First, ensure the exact token 'Answer:' occurs somewhere.
    if not RE_ANSWER_TOKEN.search(response):
        return False, (
            "Fail: The delimiter 'Answer:' is missing. Add a dedicated line containing the token and place the boxed "
            "date immediately after it, for example:\n\n**Answer:** [Date]."
        )
    # Next, ensure at least one line satisfies the immediate boxed date rule.
    if not RE_ANSWER_LINE.search(response):
        return False, (
            "Fail: 'Answer:' is present but not immediately followed by a boxed date on the same line. "
            "Use the exact pattern with a bracketed token right after it, for example:\n\n**Answer:** [Date].\n\n"
            "Place the bracketed date immediately after 'Answer:' (optionally bolded) with no other text in between."
        )
    return True, (
        "Pass: The response includes the required 'Answer:' delimiter immediately followed by a boxed date on the same line."
    )

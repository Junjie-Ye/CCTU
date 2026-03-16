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
 You must determine the answer by calling the provided tools, and your solution must involve between 3 and 5 tool calls to complete the task. The final answer must be between 5 and 10 words in length to ensure conciseness and clarity. Additionally, the final answer must be formatted using Markdown syntax, including appropriate headings and bold text to enhance clarity and structure. If the agent intends to invoke the `sports_team_venue_locator` function, the `sports_event_winner_retriever` function must be executed beforehand. If the agent intends to invoke the `stadium_info_retriever` function, the `sports_team_venue_locator` function must be executed beforehand. Parallel execution of these functions is not permitted.

response_constraints_non_length:
- idx 3: ('Response', 'Format', 'The final answer must be formatted using Markdown syntax, including appropriate headings and bold text to enhance clarity and structure.')
"""

import re
from typing import Tuple

# Helper: remove fenced code blocks and inline code to avoid false positives.


def _strip_code(text: str) -> str:
    # Remove fenced code blocks ```...```
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code `...`
    text = re.sub(r"`[^`]*`", "", text)
    return text


def _has_markdown_heading(text: str) -> bool:
    """
    Detects at least one Markdown heading line:
    - 1 to 6 leading '#' characters
    - followed by a space
    - followed by non-space content
    """
    pattern = re.compile(r"^(?:\s{0,3})(#{1,6})\s+\S.*$", re.MULTILINE)
    return bool(pattern.search(text))


def _has_bold(text: str) -> bool:
    """
    Detects Markdown bold syntax:
    - **bold** or __bold__
    Ensures there is at least one non-space character inside the markers.
    """
    bold_patterns = [
        re.compile(r"\*\*[^\s][\s\S]*?[^\s]\*\*"),  # **text**
        re.compile(r"__[^\s][\s\S]*?[^\s]__"),      # __text__
    ]
    return any(p.search(text) for p in bold_patterns)


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates that the final answer is formatted using Markdown syntax,
    including at least one heading and at least one bold segment.

    This validator checks ONLY the Markdown formatting requirements:
    - Presence of a Markdown heading (# to ######) outside code blocks.
    - Presence of bold text (**text** or __text__) outside code blocks.

    It does NOT validate other constraints (e.g., word count).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Response is empty or not a string. Provide a Markdown-formatted answer with a heading and bold text."
        )

    cleaned = _strip_code(response)
    has_heading = _has_markdown_heading(cleaned)
    has_bold = _has_bold(cleaned)

    if has_heading and has_bold:
        return (
            True,
            "Valid format: found a Markdown heading and bold text outside code blocks."
        )

    # Build detailed guidance
    missing = []
    if not has_heading:
        missing.append(
            "- Add a Markdown heading line starting with 1–6 '#' followed by a space, e.g., '# Outcome'."
        )
    if not has_bold:
        missing.append(
            "- Include at least one bold segment using **text** or __text__ (do not place it inside code fences)."
        )
    guidance = (
        "Format invalid. The response must use Markdown with a heading and bold text. "
        + " ".join(missing)
        + " Example:\n"
        + "# Result\n\n**Answer:** Your concise result here"
    )
    return (False, guidance)

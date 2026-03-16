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
 If the agent intends to invoke the `author_book_finder` tool, the `award_winner_retriever` tool must be executed beforehand. The answer must be formatted in Markdown, with the book title presented in bold text using Markdown formatting (e.g., **the target book title**).

response_constraints_non_length:
- idx 1: ('Response', 'Format', "(Response, Format, Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring the book title is presented in bold text using Markdown formatting (e.g., **All the Light We Cannot See**).))")
"""

import re
from typing import Tuple, List

# Helper: remove fenced code blocks and inline code so formatting checks
# do not consider content inside code.
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _strip_code(text: str) -> str:
    if not text:
        return text
    text = _CODE_FENCE_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    return text


# Helper: extract markdown bold segments using **...** (outside code).
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


def _extract_bold_segments(text: str) -> List[str]:
    text_wo_code = _strip_code(text)
    return [m.group(1).strip() for m in _BOLD_RE.finditer(text_wo_code)]


def _has_unbalanced_double_asterisks(text: str) -> bool:
    """
    Determine if there are stray/unmatched '**' markers outside code spans.
    Strategy:
      1) Remove all matched **...** pairs.
      2) If any '**' remains, it's unbalanced.
    """
    text_wo_code = _strip_code(text)
    text_removed_pairs = _BOLD_RE.sub("", text_wo_code)
    # If any remaining '**' (two consecutive asterisks), it's likely unbalanced.
    return "**" in text_removed_pairs


def _looks_like_title(segment: str) -> bool:
    """
    Heuristic for a plausible book title:
      - contains at least one letter
      - not purely punctuation/underscore
      - reasonable length
    We keep this permissive to avoid false negatives on single-word titles.
    """
    s = segment.strip()
    if not s:
        return False
    if len(s) > 150:
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    if re.fullmatch(r"[\W_]+", s):
        return False
    return True


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates the 'format' response constraint:
      - The response must use Markdown formatting.
      - The book title must be presented in bold using **...** (Markdown).
    Returns:
      (True, detailed_message) if valid,
      (False, detailed_instructions) if invalid.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Empty response. Provide a Markdown-formatted answer and include the target book title in bold using **Title Here**."
        )

    # Disallow using HTML tags as the only means of bolding the title.
    uses_html_bold = re.search(
        r"<\s*(b|strong)\b", response, flags=re.IGNORECASE) is not None

    bold_segments = _extract_bold_segments(response)
    has_title_bold = any(_looks_like_title(seg) for seg in bold_segments)

    # Check unbalanced '**'
    if _has_unbalanced_double_asterisks(response):
        return (
            False,
            "Unbalanced Markdown bold markers detected. Ensure every ** has a matching closing ** and do not leave stray ** outside code blocks."
        )

    # If user used only HTML bold and no Markdown bold, it's invalid.
    if uses_html_bold and not has_title_bold:
        return (
            False,
            "Do not use HTML tags like <b> or <strong> for the book title. Use Markdown bold: **Book Title**."
        )

    # Require at least one Markdown bold segment that plausibly represents a book title.
    if not has_title_bold:
        return (
            False,
            "Missing required Markdown bold for the book title. Include the target book title as **Your Book Title** somewhere in the response."
        )

    # Passed core checks: response demonstrates Markdown usage via bold title.
    # Optionally, we can also hint to avoid code fences for the title.
    return (
        True,
        "Format validated: Markdown detected and a plausible book title is bolded using **...**."
    )

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
 Your response must be formatted using Markdown syntax, must include at least one bolded sentence and a properly structured paragraph, and must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 0: ('Response', 'Format', '"The agent\'s response must be formatted using Markdown syntax, including at least one bolded sentence and a properly structured paragraph."')
- idx 1: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
"""

import re
from typing import Tuple, List

# ------------------------------
# Helper utilities
# ------------------------------

BOLD_MD_PATTERN = re.compile(
    r"(\*\*(?P<star>.+?)\*\*|__(?P<underscore>.+?)__)", re.DOTALL)

SENTENCE_END_PATTERN = re.compile(r"[.!?](?=\s|$)")

LIST_LINE_PATTERN = re.compile(r"^\s*(?:[-*+]>?|>\s*|(\d+)[\.\)])\s+")
HEADING_LINE_PATTERN = re.compile(r"^\s*#{1,6}\s+")


def _strip_markdown_inline(text: str) -> str:
    """
    Remove common inline Markdown markers to ease sentence detection.
    """
    # Remove emphasis/strong/code/backticks/links/images
    text = re.sub(r"(`+)(.+?)\1", r"\2", text)  # inline code
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", r"\1\2", text)  # bold
    text = re.sub(r"\*(.+?)\*|_(.+?)_", r"\1\2", text)  # italic
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)  # images
    text = re.sub(r"\[[^\]]*\]\([^)]+\)", r"", text)  # links
    return text


def _find_bold_segments(response: str) -> List[str]:
    """
    Return list of inner contents of bold segments (**...** or __...__).
    """
    segments = []
    for m in BOLD_MD_PATTERN.finditer(response):
        content = m.group("star") if m.group(
            "star") is not None else m.group("underscore")
        if content is not None:
            segments.append(content.strip())
    return segments


def _is_sentence(text: str) -> bool:
    """
    Heuristic: a sentence has at least one letter and ends with sentence punctuation.
    """
    t = text.strip()
    if not re.search(r"[A-Za-z]", t):
        return False
    return bool(re.search(r"[.!?]\s*$", t))


def _split_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs by blank lines.
    """
    # Normalize Windows/Mac newlines and split by 2+ newlines as paragraph delimiters
    normalized = re.sub(r"\r\n?", "\n", text)
    parts = re.split(r"\n{2,}", normalized)
    return [p.strip() for p in parts if p.strip()]


def _is_regular_paragraph(block: str) -> bool:
    """
    Determine if a block is a regular paragraph (not a header or pure list/quote)
    and contains at least one sentence.
    """
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if not lines:
        return False

    # If first non-empty line is a heading, it's not a paragraph
    if HEADING_LINE_PATTERN.match(lines[0]):
        return False

    # If all lines look like list/quote lines, it's not a paragraph
    if all(LIST_LINE_PATTERN.match(ln) for ln in lines):
        return False

    # Count sentences in the block (after stripping inline Markdown)
    cleaned = _strip_markdown_inline(block)
    # At least one sentence with terminal punctuation
    return bool(SENTENCE_END_PATTERN.search(cleaned))


# ------------------------------
# Validators
# ------------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response uses Markdown and includes at least one bolded sentence.
    - The response contains at least one properly structured paragraph
      (i.e., a normal text block, not a header or list, with at least one sentence).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Format validation failed: The response is empty. Provide a Markdown-formatted answer that includes at least one bolded sentence (e.g., **This is a key point.**) and at least one normal paragraph."
        )

    # Check for bolded segments and whether at least one is a full sentence
    bold_segments = _find_bold_segments(response)
    has_bold = len(bold_segments) > 0
    has_bold_sentence = any(_is_sentence(seg) for seg in bold_segments)

    # Check for at least one regular paragraph
    paragraphs = _split_paragraphs(response)
    has_regular_paragraph = any(_is_regular_paragraph(p) for p in paragraphs)

    issues = []
    if not has_bold:
        issues.append(
            "- Add a bolded sentence using Markdown strong emphasis. Example: **This is a key takeaway.**"
        )
    elif not has_bold_sentence:
        issues.append(
            "- Ensure at least one bolded segment is a full sentence ending with punctuation, e.g., **This is a key takeaway.**"
        )

    if not has_regular_paragraph:
        issues.append(
            "- Include at least one normal paragraph (not a header or bullet list). A paragraph should be a coherent block of text with at least one complete sentence. Separate paragraphs with a blank line if needed."
        )

    if issues:
        message = (
            "Format validation failed:\n"
            + "\n".join(issues)
            + "\nYour response must use Markdown, contain at least one bolded sentence, and include a properly structured paragraph."
        )
        return (False, message)

    return (True, "Format validation passed: The response includes Markdown with a bolded sentence and a properly structured paragraph.")


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final non-whitespace character of the response is a period (.).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Punctuation validation failed: The response is empty. End your final paragraph with a period ('.') so the last non-whitespace character is a period."
        )

    trimmed = response.rstrip()

    if trimmed.endswith("."):
        return (True, "Punctuation validation passed: The response ends with a period.")
    else:
        # Provide a tailored hint if it ends with a code fence or quote/bracket
        tail_hint = ""
        if re.search(r"```+\s*$", trimmed):
            tail_hint = " Your response appears to end with a code block. Add a concluding sentence after the code block that ends with a period."
        elif re.search(r"[\"')\]\}]\s*$", trimmed):
            tail_hint = " Place the period at the very end of the response (after any closing quotes or brackets)."

        return (
            False,
            "Punctuation validation failed: The final non-whitespace character must be a period ('.'). Add a period at the end of your last sentence." + tail_hint
        )

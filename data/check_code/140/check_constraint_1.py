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
 The answer must be presented as a complete sentence, must end with a period to ensure proper sentence closure, must include the phrase "This concludes the calculation." at the end to provide a clear and consistent ending, and must be formatted using Markdown syntax, including proper use of headings, lists, bold/italic text, and code blocks to ensure clarity and structure. The solution must involve at most 3 tool calls to ensure efficiency. Additionally, during the task, the agent must invoke at least two tool calls simultaneously in at least one interaction turn to ensure parallel processing is leveraged.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
- idx 1: ('Response', 'Format', 'The answer must be formatted using Markdown syntax, including proper use of headings, lists, bold/italic text, and code blocks to ensure clarity and structure.')
- idx 4: ('Response', 'Identifiers', 'The response must end with the phrase "This concludes the calculation." to provide a clear and consistent ending.')
"""

import re
from typing import Tuple

# Shared constants
FINAL_PHRASE = "This concludes the calculation."

# ----------------------------
# Helper functions
# ----------------------------


def _strip_trailing_whitespace(text: str) -> str:
    """Strip trailing and leading whitespace without altering internal content."""
    return text.strip()


def _remove_fenced_code_blocks(text: str) -> str:
    """Remove fenced code blocks (``` ... ```) from text to analyze prose formatting outside code."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _has_fenced_code_block(text: str) -> bool:
    """Detect presence of at least one complete fenced code block."""
    return re.search(r"```.*?```", text, flags=re.DOTALL) is not None


def _has_markdown_heading(text: str) -> bool:
    """Detect Markdown heading (# ... through ###### ...) outside code blocks."""
    for line in text.splitlines():
        if re.match(r"^\s{0,3}#{1,6}\s+\S", line):
            return True
    return False


def _has_markdown_list(text: str) -> bool:
    """Detect Markdown list items (-, *, +, or numbered '1.' style) outside code blocks."""
    for line in text.splitlines():
        if re.match(r"^\s{0,3}([-*+]\s+\S|\d+\.\s+\S)", line):
            return True
    return False


def _has_bold(text: str) -> bool:
    """Detect bold formatting using **...** outside code blocks."""
    return re.search(r"\*\*(?=\S).*?\*\*", text, flags=re.DOTALL) is not None


def _has_italic(text: str) -> bool:
    """Detect italic formatting using *...* or _..._ outside code blocks."""
    italic_asterisk = re.search(
        r"(?<!\*)\*(?=\S)(?!\*)(.*?)(?<!\*)\*(?!\*)", text, flags=re.DOTALL)
    italic_underscore = re.search(
        r"(?<!_)_(?=\S)(?!_)(.*?)(?<!_)_(?!_)", text, flags=re.DOTALL)
    return italic_asterisk is not None or italic_underscore is not None

# ----------------------------
# Validators
# ----------------------------


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    Constraint: The response must end with a period to ensure proper sentence closure.
    """
    trimmed = _strip_trailing_whitespace(response)
    if len(trimmed) == 0:
        return (
            False,
            "The response is empty. Provide a complete sentence and ensure the very last character is a period '.'."
        )

    if trimmed.endswith("."):
        return (
            True,
            "The response ends with a period; punctuation constraint satisfied."
        )
    else:
        return (
            False,
            "End the final sentence with a period '.' as the very last character of the entire response. "
            "If the response currently ends with a code fence (```), a quote, or any other punctuation, add a final line "
            "after all content that concludes with a period. Example fix: append a final sentence that ends with '.'."
        )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - Headings
    - Lists
    - Bold text
    - Italic text
    - Fenced code blocks

    Constraint: The answer should be formatted using Markdown syntax.
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Provide an answer with at least one Markdown element: heading, list, bold, italic, or code block."
        )

    trimmed = _strip_trailing_whitespace(response)
    prose = _remove_fenced_code_blocks(trimmed)

    has_heading = _has_markdown_heading(prose)
    has_list = _has_markdown_list(prose)
    has_bold = _has_bold(prose)
    has_italic = _has_italic(prose)
    has_code_block = _has_fenced_code_block(trimmed)

    # OR logic: At least one element must be present
    has_any_formatting = has_heading or has_list or has_bold or has_italic or has_code_block

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Summary' or '## Results')\n"
            "2. A list (e.g., '- Item' or '1. Step')\n"
            "3. Bold text (e.g., **important**)\n"
            "4. Italic text (e.g., *emphasis* or _note_)\n"
            "5. A fenced code block (```code```)\n\n"
            "Example minimal format: '# Analysis' (just a heading is sufficient)"
        )

    # Build feedback on what was found and missing
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append(
            "Add a heading line starting with '# ' (e.g., '# Summary').")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append(
            "Include a list with items prefixed by '-', '*', '+', or numbers like '1.'.")

    if has_bold:
        found_elements.append("bold text")
    else:
        suggestions.append(
            "Apply bold formatting using **bold** around important words.")

    if has_italic:
        found_elements.append("italic text")
    else:
        suggestions.append(
            "Apply italic formatting using *italic* or _italic_ for emphasis.")

    if has_code_block:
        found_elements.append("code block")
    else:
        suggestions.append(
            "Add a fenced code block using triple backticks (```).")

    # Build response message
    success_msg = f"The response includes {', '.join(found_elements)}."

    if suggestions:
        success_msg += "\n\nFor improved formatting, consider adding:\n" + \
            "\n".join([f"- {s}" for s in suggestions])

    return (True, success_msg)


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the exact phrase 'This concludes the calculation.'.
    Constraint: The response must end with the phrase "This concludes the calculation." to provide a clear and consistent ending.
    """
    trimmed = _strip_trailing_whitespace(response)
    if trimmed.endswith(FINAL_PHRASE):
        return (
            True,
            "The response ends with the exact required phrase; identifier constraint satisfied."
        )
    else:
        # Provide precise guidance on appending the phrase correctly.
        return (
            False,
            "Append the exact phrase 'This concludes the calculation.' as the final text of the response, "
            "with the same capitalization and including the final period. Place it after all content (including any code blocks), "
            "and ensure there is no extra text, whitespace, or punctuation after the period. Example fix: add a final line: "
            "'This concludes the calculation.'"
        )

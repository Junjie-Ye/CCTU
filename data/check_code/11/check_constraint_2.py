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
 Your response must be formatted entirely using Markdown syntax, including appropriate use of bold, headings, or other elements to clearly present the answer. Additionally, ensure the response ends with a period to maintain proper sentence closure. The response must begin with the phrase "**The answer is: **" followed by the answer in bold formatting to ensure a clear and recognizable opening. You may use each tool type at most 2 times during your problem-solving process to ensure efficient use of available functions. Importantly, you must complete this task with a total of no more than 3 tool calls across all interaction turns to demonstrate efficient problem-solving.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 1: ('Response', 'Punctuation', 'Ending punctuation is a period.')
- idx 2: ('Response', 'Identifiers', 'The response must begin with the phrase "**The answer is: **" followed by the answer in bold formatting, ensuring a clear and consistent opening that highlights the response.')
"""

import re
from typing import Tuple

# ---------------------------
# Shared helpers and patterns
# ---------------------------

# Exact required opening phrase (including spacing) in Markdown bold
REQUIRED_OPENING_BOLD_PHRASE = r"^\s*\*\*The answer is: \*\*"
opening_phrase_re = re.compile(REQUIRED_OPENING_BOLD_PHRASE)

# Bold segment pattern like **text**, text must be non-empty and not only whitespace
bold_segment_re = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")

# Headings, lists, links, code indicators to detect general Markdown usage
md_heading_re = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
md_list_re = re.compile(r"^(\*|\-|\+|\d+\.)\s+\S", re.MULTILINE)
md_link_re = re.compile(r"\[[^\]]+\]\([^)]+\)")
md_inline_code_re = re.compile(r"`[^`]+`")
md_code_fence_re = re.compile(r"```")


def _last_visible_char_for_punctuation(text: str) -> str:
    """
    Returns the last visible character for punctuation checking,
    ignoring trailing whitespace and trailing Markdown emphasis markers (*, _).
    Does NOT strip code fences/backticks; they must not end the response.
    """
    s = text.rstrip()

    # Strip trailing paired markdown emphasis markers like ** and __ repeatedly
    while s.endswith("**") or s.endswith("__"):
        s = s[:-2].rstrip()

    # Strip single trailing emphasis markers if any remain
    while s.endswith("*") or s.endswith("_"):
        s = s[:-1].rstrip()

    return s[-1] if s else ""


def _has_any_markdown_feature(text: str) -> bool:
    """
    Returns True if the text appears to use any Markdown feature:
    - bold/italic
    - headings
    - lists
    - links
    - inline code
    - fenced code blocks
    """
    if bold_segment_re.search(text):
        return True
    if md_heading_re.search(text):
        return True
    if md_list_re.search(text):
        return True
    if md_link_re.search(text):
        return True
    if md_inline_code_re.search(text):
        return True
    if md_code_fence_re.search(text):
        # also consider fenced code blocks as Markdown usage
        return True
    return False


def _has_balanced_code_fences(text: str) -> bool:
    """
    Ensures the number of triple-backtick code fences is even (balanced).
    """
    return len(md_code_fence_re.findall(text)) % 2 == 0

# -----------------------------------
# Constraint-specific validator APIs
# -----------------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The entire response is presented using Markdown (at least one Markdown element present).
    - No unbalanced fenced code blocks.
    This function focuses on structural Markdown usage; the opening phrase and punctuation
    are validated in their dedicated validators.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a non-empty Markdown-formatted response."
        )

    if not _has_any_markdown_feature(response):
        return (
            False,
            "No Markdown features detected. Use Markdown elements (e.g., bold, headings, lists, links, or code). "
            'At minimum, include the required bold opening phrase and a bold answer, e.g.: "**The answer is: ** **your answer here**."'
        )

    if not _has_balanced_code_fences(response):
        return (
            False,
            "Unbalanced triple backtick code fences detected. Ensure that code blocks start and end with matching ``` fences."
        )

    return (
        True,
        "The response uses Markdown features and code fences appear balanced."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period as the final visible character,
    allowing for trailing Markdown emphasis markers like ** or * after the period (e.g., **Yes.**).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. It must end with a period."
        )

    # If response ends with backticks (inline or fenced), this violates the period rule.
    trimmed = response.rstrip()
    if trimmed.endswith("```") or trimmed.endswith("`"):
        return (
            False,
            "The response ends with backticks. Place a period at the end of the sentence (outside code blocks) so the final visible character is a period."
        )

    last_char = _last_visible_char_for_punctuation(response)
    if last_char != ".":
        return (
            False,
            "The response must end with a period. Ensure the final visible character is '.'. "
            "If you used bold or italic at the end, put the period before the closing formatting markers, e.g., **Answer.**"
        )

    return (
        True,
        "The response ends with a period as required."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response begins with the exact phrase '**The answer is: **' (including spaces) at the very start (ignoring leading whitespace).
    - The phrase is immediately followed (optionally after whitespace) by a bold answer '**...**' with non-empty content.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            'The response is empty or not a string. It must start with the exact phrase "**The answer is: **" followed by a bold answer.'
        )

    m = opening_phrase_re.match(response)
    if not m:
        return (
            False,
            'The response must start with the exact phrase "**The answer is: **" (including the colon and trailing space inside the bold). '
            'Example: "**The answer is: ** **Your concise answer here.**"'
        )

    remainder = response[m.end():]
    # Allow whitespace between the opening phrase and the bold answer
    remainder = remainder.lstrip()

    # The next token must be a bold segment **...**
    bold_match = bold_segment_re.match(remainder)
    if not bold_match:
        return (
            False,
            'After the opening phrase, provide the answer in bold as "**Your answer here**". '
            'Example: "**The answer is: ** **Your concise answer here.**"'
        )

    # Ensure bold content is non-empty (regex already enforces non-whitespace)
    bold_content = bold_match.group(1)
    if not bold_content.strip():
        return (
            False,
            "The bold answer segment is empty. Put non-empty content between the '**' markers."
        )

    return (
        True,
        'The response begins with the required "**The answer is: **" phrase and is followed by a bold answer.'
    )

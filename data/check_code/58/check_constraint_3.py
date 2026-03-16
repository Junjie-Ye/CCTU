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
 The agent must not call the 'cultural_information_retriever' tool more than 2 times during the process. The tool 'workshop_locator' must be called after the tool 'business_locator' in the execution sequence. The agent must complete the task in a number of interaction turns that falls within the range of 6 to 8 (inclusive). The agent's final response must be formatted using Markdown syntax, including appropriate headings and bold text for clarity and structure, and must end with a period (.) to ensure proper sentence closure.

response_constraints_non_length:
- idx 3: ('Response', 'Format', "The agent's final response must be formatted using Markdown syntax, including appropriate headings and bold text for clarity and structure.")
- idx 4: ('Response', 'Punctuation', "The agent's final response must end with a period (.) to ensure proper sentence closure.")
"""

import re
from typing import Tuple

# Helper utilities


def _strip_fenced_and_inline_code(text: str) -> str:
    """
    Remove fenced code blocks (``` or ~~~) and inline code (`...`) so that
    Markdown structure (headings/bold) can be validated on prose only.
    """
    if not text:
        return text
    # Remove fenced code blocks with backticks or tildes
    text_wo_fenced = re.sub(r"```[\s\S]*?```", "", text, flags=re.DOTALL)
    text_wo_fenced = re.sub(r"~~~[\s\S]*?~~~", "",
                            text_wo_fenced, flags=re.DOTALL)
    # Remove inline code spans
    text_wo_code = re.sub(r"`[^`]*`", "", text_wo_fenced)
    return text_wo_code


def _has_markdown_heading(text: str) -> bool:
    """
    Detect at least one Markdown heading line like '# Title' up to '###### Title'.
    Ignores headings inside code thanks to prior stripping.
    """
    return re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", text) is not None


def _has_markdown_bold(text: str) -> bool:
    """
    Detect at least one bold segment using **...** or __...__.
    Ignores bold inside code thanks to prior stripping.
    """
    return re.search(r"(\*\*[^*\n][\s\S]*?\*\*)|(__[^_\n][\s\S]*?__)", text) is not None


# Validators for response constraints

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response:
    - Uses Markdown syntax with at least one heading.
    - Includes bold text for clarity (e.g., **Key Term** or __Key Term__).
    Returns:
      (True, message) if valid;
      (False, actionable_message) if invalid.
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Provide a Markdown-formatted final answer with at least one heading (e.g., '## Overview') and bold emphasis (e.g., '**Key Insight:** ...'). Ensure these elements appear in the prose, not inside code blocks."
        )

    prose = _strip_fenced_and_inline_code(response)

    has_heading = _has_markdown_heading(prose)
    has_bold = _has_markdown_bold(prose)

    if has_heading and has_bold:
        return (
            True,
            "Valid format: Markdown headings and bold text are present."
        )

    if not has_heading and not has_bold:
        return (
            False,
            "Invalid format: no Markdown headings or bold text detected. Add at least one heading line using '#', '##', ..., '######' (e.g., '## Findings') and include bold emphasis using **...** or __...__ (e.g., '**Methodology:** Mixed methods'). Place these elements in the prose (not inside code blocks)."
        )

    if not has_heading:
        return (
            False,
            "Invalid format: no Markdown headings detected. Add at least one heading line using '#', '##', ..., '######' (e.g., '## Findings'). Ensure the heading is in the prose and not inside a code block."
        )

    # not has_bold
    return (
        False,
        "Invalid format: no bold text detected. Use **...** or __...__ to highlight key labels or terms (e.g., '**Key Insight:** ...'). Ensure the bold text appears in the prose and not inside a code block."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period '.' character.
    Returns:
      (True, message) if valid;
      (False, actionable_message) if invalid.
    """
    if not response or not response.strip():
        return (
            False,
            "Empty or whitespace-only response. Provide a final answer sentence that ends with a period '.'."
        )

    stripped = response.rstrip()

    if stripped.endswith('.'):
        return (
            True,
            "Valid punctuation: the response ends with a period '.' as required."
        )

    # Special guidance if the response ends with a code fence
    if stripped.endswith("```") or stripped.endswith("~~~"):
        return (
            False,
            "The response ends with a code fence marker rather than a period. Add a concluding sentence after the code block that ends with a period '.' (e.g., 'This concludes the findings.'). Ensure no extra characters follow the final period."
        )

    last_char = stripped[-1]
    if last_char in {'。', '!', '?', '!', '?', ';', '...', ':'}:
        return (
            False,
            f"The last visible character is '{last_char}', not a period '.'. Replace it or append a final sentence so the very last character of the entire response is a period '.', with no trailing whitespace or Markdown tokens."
        )

    return (
        False,
        "The response does not end with a period '.'. Edit the final line so the last visible character of the entire response is a period '.', avoiding any trailing whitespace or Markdown markers after it."
    )

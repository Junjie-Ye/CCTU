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
 The answer must be formatted using Markdown syntax, ensuring the use of headings, bold text, and bullet points to clearly outline each step in the solution process. Additionally, the agent's response must start with the identifier "### Final Answer:" to clearly denote the final answer section. The response must be at least 500 characters in length to ensure detailed explanations and structured formatting.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must be formatted using Markdown syntax, ensuring the use of headings, bold text, and bullet points to clearly outline each step in the solution process.')
- idx 1: ('Response', 'Identifiers', 'The agent\'s response must start with the identifier "### Final Answer:"')
"""

import re
from typing import Tuple

# Helper: remove fenced and inline code to avoid false positives when scanning Markdown features


def _strip_code_regions(text: str) -> str:
    # Remove fenced code blocks ```...```
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove inline code `...`
    text = re.sub(r"`[^`]*`", "", text)
    return text


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - Headings (# ...)
    - Bold text (**bold**)
    - Bullet points (-, *, +)

    Returns (bool, message).
    """
    if not response or not response.strip():
        return False, "Response is empty. Include at least one Markdown element: heading, bold text, or bullet points."

    scanned = _strip_code_regions(response)

    has_heading = re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", scanned) is not None
    # Robust bold pattern: at least one non-space between ** and **, not only spaces
    has_bold = re.search(r"\*\*(?=\S)(?:.+?)(?<=\S)\*\*",
                         scanned, flags=re.DOTALL) is not None
    has_bullets = re.search(r"(?m)^\s{0,3}[-*+]\s+\S", scanned) is not None

    # OR logic: At least one element must be present
    has_any_formatting = has_heading or has_bold or has_bullets

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. Bold text using **bold** (e.g., '**Important**')\n"
            "3. Bullet points using '-', '*', or '+' (e.g., '- Item 1')\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Record what was found and provide suggestions
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append("Consider adding a heading for structure.")

    if has_bold:
        found_elements.append("bold text")
    else:
        suggestions.append("Consider using **bold** for emphasis.")

    if has_bullets:
        found_elements.append("bullet points")
    else:
        suggestions.append("Consider adding bullet points for lists.")

    # Build response message
    if suggestions:
        return (
            True,
            f"Format acceptable: Found {', '.join(found_elements)}. "
            f"Suggestions: {' '.join(suggestions)}"
        )
    else:
        return (
            True,
            f"Format excellent: Found {', '.join(found_elements)}."
        )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response starts exactly with the identifier '### Final Answer:'.
    Returns (bool, message).
    """
    required = "### Final Answer:"
    if response.startswith(required):
        return True, "Validation passed: The response begins with the exact identifier '### Final Answer:'."

    # Check for common near-miss cases
    if response.lstrip().startswith(required) and not response.startswith(required):
        return (
            False,
            "Validation failed: The identifier must be the very first characters of the response with no leading spaces or newlines. "
            "Remove any leading whitespace so the content starts exactly with '### Final Answer:'."
        )

    if response.startswith("### Final Answer") and not response.startswith(required):
        return (
            False,
            "Validation failed: The identifier is missing the trailing colon. Start the message with exactly '### Final Answer:' followed by a newline."
        )

    idx = response.find(required)
    if idx != -1 and idx > 0:
        return (
            False,
            f"Validation failed: The identifier '### Final Answer:' appears at position {idx}, but it must be at position 0. "
            "Move it to the very start of the response with no preceding text or whitespace."
        )

    return (
        False,
        "Validation failed: The response must start with the exact identifier '### Final Answer:'. "
        "Begin your message with '### Final Answer:' on the first line, then follow with your Markdown-formatted content."
    )

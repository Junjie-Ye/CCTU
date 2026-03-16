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
 You must follow these constraints: If the agent intends to invoke the 'paleontological_discovery_locator', the 'paleontologist_discovery_finder' must strictly be executed beforehand. Additionally, your final response must end with the phrase 'Final Answer: [traditional dessert name]' and the entire response must be formatted using Markdown syntax with proper use of headings, bold/italic text, lists, and code blocks for clarity. The tool 'paleontologist_discovery_finder' must be called at most 1 time during the solution process.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', "The agent's response must end with the phrase 'Final Answer: [dessert name]' where [dessert name] is replaced with the actual dessert name")
- idx 2: ('Response', 'Format', "The agent's response must be formatted using Markdown syntax, including headings, bold/italic text, and code blocks to enhance readability")
"""

import re
from typing import Tuple

# -----------------------------
# Helper functions
# -----------------------------


def _last_nonempty_line(text: str) -> str:
    """
    Return the last non-empty line from the text. If none, return an empty string.
    """
    for line in reversed(text.splitlines()):
        if line.strip():
            return line
    return ""


def _has_markdown_heading(text: str) -> bool:
    """
    Detect if there is at least one Markdown heading (# ... up to ######).
    """
    return re.search(r'(?m)^\s{0,3}#{1,6}\s+\S', text) is not None


def _has_bold_or_italic(text: str) -> bool:
    """
    Detect if there is at least one bold or italic segment:
    - Bold: **text** or __text__
    - Italic: *text* or _text_ (but not part of bold markers)
    """
    bold = re.search(r'(\*\*|__)(?=\S)(.+?)(?<=\S)\1', text) is not None
    italic = re.search(
        r'(?<!\*)\*(?=\S)(.+?)(?<=\S)\*(?!\*)|(?<!_)_(?=\S)(.+?)(?<=\S)_(?!_)',
        text
    ) is not None
    return bold or italic


def _has_balanced_code_blocks(text: str) -> Tuple[bool, int]:
    """
    Check for at least one fenced code block using triple backticks and ensure fences are balanced.
    Returns (is_balanced_and_present, fence_count).
    """
    # Count all fence lines that start with ```
    fences = re.findall(r'(?m)^\s*```', text)
    balanced = (len(fences) % 2 == 0)
    has_block = re.search(r'(?s)(?m)^\s*```.*?^\s*```', text) is not None
    return (balanced and has_block), len(fences)

# -----------------------------
# Validators
# -----------------------------


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the final non-empty line is exactly:
    **Final Answer: <dessert name>**
    where <dessert name> is a non-empty, bracket-free plain string.
    """
    last_line = _last_nonempty_line(response).strip()

    # Must be fully bolded and follow the pattern inside **...**
    m = re.match(r'^\*\*\s*Final Answer:\s*(.+?)\s*\*\*\s*$', last_line)
    if not m:
        return (
            False,
            "The response must end with a final non-empty line exactly like "
            "**Final Answer: <traditional dessert name>** (including the surrounding ** **). "
            "Example: **Final Answer: Tiramisu**."
        )

    dessert = m.group(1).strip()

    if not dessert:
        return (
            False,
            "The final line is bolded but the dessert name is missing. "
            "Example: **Final Answer: Baklava**."
        )

    # still forbid placeholder brackets
    if '[' in dessert or ']' in dessert:
        return (
            False,
            "Replace the placeholder with a real dessert name (no square brackets). "
            "Example: **Final Answer: Mochi**."
        )

    # forbid code formatting or nested bold markers in the dessert name
    if '`' in dessert:
        return (
            False,
            "Do not include backticks or code formatting in the dessert name on the final line. "
            "Use plain text, e.g., **Final Answer: Cannoli**."
        )

    if '**' in dessert or '__' in dessert:
        return (
            False,
            "Do not nest additional bold markers inside the final bold line. "
            "Keep only the outer **...** around the whole line."
        )

    return True, "OK: The response ends with a fully bolded '**Final Answer: <dessert name>**' line."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (#, ##, ..., ######)
    - Bold or italic text
    - A fenced code block (``` ... ```) with balanced fences
    """
    if not response or not response.strip():
        return (
            False,
            "Response is empty. Include at least one Markdown element: heading, bold/italic, or code block."
        )

    # Check for each element
    has_heading = _has_markdown_heading(response)
    has_emphasis = _has_bold_or_italic(response)
    balanced_code, fence_count = _has_balanced_code_blocks(response)

    # OR logic: at least one element must be present
    has_any_markdown = has_heading or has_emphasis or balanced_code

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n"
            "- A heading (e.g., '# Title' or '## Section')\n"
            "- Bold or italic text (e.g., **important** or *note*)\n"
            "- A fenced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Optional warnings for specific elements (not errors)
    suggestions = []
    found_elements = []

    if has_heading:
        found_elements.append("heading")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("Consider adding bold or italic text for emphasis.")

    if balanced_code:
        found_elements.append("code block")
    elif fence_count > 0:
        # Special case: has code fences but unbalanced
        suggestions.append(
            "Fix unbalanced code fences: ensure every ``` has a matching closing ```.")
    else:
        suggestions.append(
            "Consider adding a code block for structured content.")

    success_msg = f"OK: Found {', '.join(found_elements)}."
    if suggestions:
        success_msg += " Suggestions: " + " ".join(suggestions)

    return True, success_msg

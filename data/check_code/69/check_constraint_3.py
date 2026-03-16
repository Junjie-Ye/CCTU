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
 You must use at least 5 interaction turns. If the agent intends to invoke the specified tools, the execution must follow the exact sequence: business_magnate_identifier, historical_company_finder, company_device_inquiry, tech_phenomenon_mapper_v2, scientific_discovery_lookup, historical_figure_locator, regional_cuisine_identifier. Your final answer must be formatted using Markdown syntax with appropriate headings and bullet points, concluding with the phrase "Final Answer: [target dessert]" where [target dessert] is replaced with the identified dessert.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Main Category, Response, End identifier (Mandates that the agent\'s response must conclude with the phrase "Final Answer: [dessert name]" followed by a punctuation mark where [dessert name] is replaced with the specific dessert identified through tool calls.))')
- idx 2: ('Response', 'Punctuation', "(Main Category, Response, Ending punctuation (.) (Specifies that the agent's response must end with a period to ensure proper sentence closure.))")
- idx 3: ('Response', 'Format', "(Main Category, Response, Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.))")
"""

import re
from typing import Tuple, Optional

# ---------------------------
# Helper utilities
# ---------------------------

HEADING_RE = re.compile(r'^\s{0,3}#{1,6}\s+\S', re.MULTILINE)
BULLET_LIST_RE = re.compile(r'^\s{0,3}([-*+])\s+\S', re.MULTILINE)
NUMBERED_LIST_RE = re.compile(r'^\s{0,3}\d+\.\s+\S', re.MULTILINE)
FINAL_ANSWER_LINE_RE = re.compile(
    r'^\s*Final Answer:\s*(?P<dessert>.+?)(?P<punc>[.!?;:,])\s*$'
)


def _last_nonempty_line(text: str) -> Optional[str]:
    """Return the last non-empty (non-whitespace) line, or None if none exists."""
    for line in reversed(text.splitlines()):
        if line.strip():
            return line.rstrip()
    return None


def _has_markdown_heading(text: str) -> bool:
    return bool(HEADING_RE.search(text))


def _has_markdown_list(text: str) -> bool:
    return bool(BULLET_LIST_RE.search(text) or NUMBERED_LIST_RE.search(text))


def _code_fences_balanced(text: str) -> bool:
    """
    Consider a code fence to be any line that starts with three backticks.
    Balanced if count is 0 or even.
    """
    fence_count = sum(1 for line in text.splitlines()
                      if line.strip().startswith("```"))
    return fence_count % 2 == 0


def _find_final_answer_line(text: str) -> Optional[re.Match]:
    """
    Return a regex Match object for the last non-empty line if it matches the
    'Final Answer: <dessert><punc>' pattern; otherwise None.
    """
    last = _last_nonempty_line(text)
    if last is None:
        return None
    return FINAL_ANSWER_LINE_RE.match(last)


# ---------------------------
# Validators (as requested)
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - At least one Markdown heading (#, ##, ...)
    - At least one list item (bulleted -, *, + or numbered "1. ")
    - If code fences are used, they must be balanced.

    Note: Final line requirements are validated separately.
    """
    if not response or not response.strip():
        return (False, "The response is empty. Provide an answer with at least one formatting element: heading, list, or properly balanced code blocks.")

    has_heading = _has_markdown_heading(response)
    has_list = _has_markdown_list(response)
    fences_ok = _code_fences_balanced(response)
    has_fences = "```" in response

    # OR logic: At least one formatting element must be present
    has_any_formatting = has_heading or has_list or (has_fences and fences_ok)

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n"
            "1. A heading (e.g., '# Title' or '## Results')\n"
            "2. A list (e.g., '- item' or '1. step')\n"
            "3. A properly balanced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Check for specific issues
    issues = []
    suggestions = []
    found_elements = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append("Consider adding a heading for structure.")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append("Consider adding a list for organization.")

    if has_fences:
        if fences_ok:
            found_elements.append("balanced code block")
        else:
            issues.append(
                "Code fences are unbalanced. Ensure every '```' opening has a corresponding closing '```'.")
    else:
        suggestions.append("Consider adding a code block for examples.")

    # Build response message
    if issues:
        # Has issues but still passes (OR logic)
        return (
            True,
            f"Format acceptable: Found {', '.join(found_elements)}. "
            f"Issues to fix: {' '.join(issues)}. "
            f"Suggestions: {' '.join(suggestions) if suggestions else 'None'}"
        )
    elif suggestions:
        return (
            True,
            f"Format valid: Found {', '.join(found_elements)}. "
            f"Suggestions: {' '.join(suggestions)}"
        )
    else:
        return (
            True,
            f"Format excellent: Found {', '.join(found_elements)}."
        )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the entire response ends with a period '.' (after trimming trailing whitespace).
    """
    if response is None or not response.strip():
        return (False, "The response is empty. Provide content and ensure it ends with a period '.' after the 'Final Answer: <dessert>' line.")

    trimmed = response.rstrip()
    if trimmed.endswith('.'):
        return (True, "Ending punctuation validated: response ends with a period '.'.")

    # Identify if it ends with other punctuation
    last_char = trimmed[-1]
    if last_char in ['!', '?', ';', ':', ',']:
        return (
            False,
            f"The response ends with '{last_char}'. It must end with a period '.'. Replace the final character with '.' so the final line reads like 'Final Answer: <dessert>.'"
        )

    return (
        False,
        "The response does not end with a period '.'. Append a '.' at the very end, immediately after the 'Final Answer: <dessert>' line."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with:
      Final Answer: <dessert><punctuation>
    where <dessert> is a non-empty, concrete dessert name (no placeholders),
    and <punctuation> is any punctuation mark (e.g., '.', '!', '?', ';', ':', ',').
    This line must be the last non-empty line in the response.
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. End your Markdown response with a final line: 'Final Answer: <dessert>.' where <dessert> is the specific dessert name."
        )

    match = _find_final_answer_line(response)
    if not match:
        last_line = _last_nonempty_line(response) or ""
        if "Final Answer:" in response and not last_line.strip().startswith("Final Answer:"):
            return (
                False,
                "The response must conclude with a line starting with 'Final Answer:'. Move the 'Final Answer: <dessert>.' line to be the final non-empty line of the response."
            )
        # Could be missing punctuation or malformed format
        if last_line.strip().startswith("Final Answer:"):
            return (
                False,
                "The final line starts with 'Final Answer:' but is malformed. Use the exact pattern 'Final Answer: <dessert><punctuation>'. Example: 'Final Answer: Tiramisu.'"
            )
        return (
            False,
            "Append a final identifier line at the very end using: 'Final Answer: <dessert><punctuation>'. Example: 'Final Answer: Tiramisu.'"
        )

    dessert = match.group("dessert").strip()
    punc = match.group("punc")

    # Ensure dessert is not a placeholder or empty
    placeholder_signals = [
        "[", "]", "target dessert", "dessert name"
    ]
    if not dessert or any(sig in dessert.lower() for sig in placeholder_signals):
        return (
            False,
            "Replace placeholders with a concrete dessert name derived from verified tool outputs. Example final line: 'Final Answer: Tiramisu.'"
        )

    # If there is any content after the final line (shouldn't be by definition), nudge anyway
    last_line = _last_nonempty_line(response) or ""
    if not FINAL_ANSWER_LINE_RE.match(last_line):
        return (
            False,
            "Ensure the 'Final Answer: <dessert><punctuation>' line is the final non-empty line. Remove or move any trailing content after it."
        )

    return (
        True,
        f"Identifier validated: final line matches 'Final Answer: {dessert}{punc}'."
    )

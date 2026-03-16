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
 The answer must be formatted using Markdown syntax to ensure proper use of elements such as headings, lists, bold/italic text, and code blocks to enhance readability and structure. The tool 'orchestra_conductor_finder' can be used at most once. The tool 'regional_cuisine_explorer' can be used at most once. The final answer must start with the identifier "**Final Answer:**" followed by a colon and a space. The final answer must end with a period. The response must be between 500 and 1000 characters in length, measured by character count, to ensure it is concise yet sufficiently detailed.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "(Response, Format, Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.))")
- idx 2: ('Response', 'Identifiers', '(Main Category, Start identifier, The final answer must start with the identifier "**Final Answer:**" followed by a colon and a space.)')
- idx 3: ('Response', 'Punctuation', 'The final answer must end with a period.')
"""

import re
from typing import Tuple, Dict

# Helper: detect common Markdown features in the response


def _detect_markdown_features(text: str) -> Dict[str, bool]:
    has_heading = re.search(r'^\s*#{1,6}\s+\S', text, re.MULTILINE) is not None
    has_list = re.search(
        r'^\s*(?:[-*+]\s+\S|\d+\.\s+\S)', text, re.MULTILINE) is not None
    has_bold = re.search(r'\*\*[^*\n]+\*\*', text, re.DOTALL) is not None
    # Match italic while avoiding bold (**text**) collisions; supports *text* or _text_
    has_italic = re.search(
        r'(?<!\*)\*[^*\n]+\*(?!\*)|_[^_\n]+_', text, re.DOTALL) is not None
    has_emphasis = has_bold or has_italic
    has_code_fence = re.search(r'```[\s\S]*?```', text) is not None
    fence_count = len(re.findall(r'```', text))
    fences_balanced = (fence_count % 2 == 0)
    has_link = re.search(r'\[[^\]]+\]\([^)]+\)', text) is not None
    return {
        "has_heading": has_heading,
        "has_list": has_list,
        "has_emphasis": has_emphasis,
        "has_code_fence": has_code_fence,
        "fences_balanced": fences_balanced,
        "has_link": has_link,
    }


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates that the response contains at least ONE core Markdown element:
    - Headings (# ...)
    - Lists (-, 1., etc.)
    - Emphasis (bold/italic)

    Code fences must be balanced if present.
    Links and code blocks are optional but recommended.
    """
    if not response or not response.strip():
        return (False, "Empty response. Provide an answer with at least one Markdown element: heading, list, or emphasis.")

    features = _detect_markdown_features(response)

    # Collect feedback
    issues = []
    suggestions = []
    found_elements = []

    # Core elements
    if features["has_heading"]:
        found_elements.append("heading")
    else:
        suggestions.append(
            "Consider adding a heading (e.g., '# Overview') for structure.")

    if features["has_list"]:
        found_elements.append("list")
    else:
        suggestions.append(
            "Consider adding a list (e.g., '- Item') for organization.")

    if features["has_emphasis"]:
        found_elements.append("emphasis")
    else:
        suggestions.append(
            "Consider using emphasis (e.g., **bold** or *italic*).")

    # OR logic: At least one core element must be present
    has_any_core_element = features["has_heading"] or features["has_list"] or features["has_emphasis"]

    if not has_any_core_element:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these core elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. A list (e.g., '- Item' or '1. Step')\n"
            "3. Emphasis (e.g., **bold** or *italic*)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Code fence balance (required if fences are present)
    if features["has_code_fence"] and not features["fences_balanced"]:
        issues.append(
            "Close all fenced code blocks properly: use matching triple backticks ``` for open and close.")

    # Optional recommendations
    if not features["has_link"]:
        suggestions.append(
            "Consider adding links [text](url) for references (optional).")

    if not features["has_code_fence"]:
        suggestions.append(
            "Consider adding code blocks ``` for examples (optional).")

    # Build response message
    if issues:
        # Has issues (like unbalanced fences) but still passes (OR logic)
        return (
            True,
            f"Format acceptable (with issues): Found {', '.join(found_elements)}. "
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


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response starts with the required start identifier:
    '**Final Answer:** ' (bold text including the colon, followed by a single space).
    """
    expected_prefix = "**Final Answer:** "
    starts_exact = response.startswith(expected_prefix)
    starts_after_whitespace = response.lstrip().startswith(expected_prefix)

    if starts_exact:
        return (True, "Start identifier is correctly placed and formatted.")
    elif starts_after_whitespace:
        return (False,
                "The start identifier is correct but preceded by leading whitespace. "
                "Remove any whitespace before the exact prefix: '**Final Answer:** '.")
    else:
        # Diagnose common near-misses
        if response.startswith("Final Answer: "):
            return (False,
                    "The start identifier is missing bold formatting. Begin the response EXACTLY with '**Final Answer:** ' "
                    "(two asterisks on both sides, colon inside the bold, one space after).")
        if response.startswith("**Final Answer:**") and not response.startswith(expected_prefix):
            return (False,
                    "Add a single space immediately after the bold identifier. The response must start with '**Final Answer:** ' (note the trailing space).")
        return (False,
                "Begin the response EXACTLY with '**Final Answer:** ' at the very first character (no leading whitespace). "
                "Use bold (**), include the colon inside the bold, and add one space after the identifier.")


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the final answer ends with a period. Trailing whitespace is ignored.
    """
    trimmed = response.rstrip()
    if not trimmed:
        return (False, "The response is empty. Provide content that ends with a single period.")
    if trimmed.endswith('.'):
        return (True, "The response correctly ends with a period.")
    else:
        last_char = trimmed[-1]
        if last_char in ['!', '?', '`']:
            return (False,
                    "The response must end with a period. Replace the final '{}' with a '.' "
                    "and ensure the period is the last character after any closing Markdown blocks.".format(last_char))
        return (False,
                "Append a '.' at the very end of the response (after any text, lists, or code blocks) so the final character is a period.")

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
 If the agent intends to invoke the `space_agency_locator`, the `geographic_feature_locator` must strictly be executed beforehand. If the agent intends to invoke the `satellite_launch_info_retriever`, the `space_agency_locator` must strictly be executed beforehand. If the agent intends to invoke the `corporate_partnership_finder`, the `satellite_launch_info_retriever` must strictly be executed beforehand. If the agent intends to invoke the `software_algorithm_identifier`, the `corporate_partnership_finder` must strictly be executed beforehand. If the agent intends to invoke the `algorithm_insight_extractor`, the `software_algorithm_identifier` must strictly be executed beforehand. If the agent intends to invoke the `math_formula_origin_finder`, the `algorithm_insight_extractor` must strictly be executed beforehand. If the agent intends to invoke the `biographical_info_finder`, the `math_formula_origin_finder` must strictly be executed beforehand. If the agent intends to invoke the `cuisine_explorer`, the `biographical_info_finder` must strictly be executed beforehand. If the agent intends to invoke the `culinary_ingredient_identifier`, the `cuisine_explorer` must strictly be executed beforehand. Each tool can be used at most once in the entire solution process. The final answer must end with a period to ensure sentence closure and clarity, and it must be formatted in **Markdown** syntax, with clear headings, bullet points, and emphasized terms to ensure clarity and structure.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The final answer must end with a period to ensure sentence closure and clarity.')
- idx 2: ('Response', 'Format', 'The answer must be formatted in Markdown syntax, with clear headings, bullet points, and emphasized terms to ensure clarity and structure.')
"""

import re
from typing import Tuple

# Helper regex patterns for Markdown features
HEADING_PATTERN = re.compile(r'^\s{0,3}#{1,6}\s+\S', re.MULTILINE)
BULLET_PATTERN = re.compile(r'^\s{0,3}([-*+])\s+\S', re.MULTILINE)
NUMBERED_LIST_PATTERN = re.compile(r'^\s{0,3}\d+\.\s+\S', re.MULTILINE)
EMPHASIS_PATTERN = re.compile(
    r'(\*\*[^*\n]+?\*\*)'        # bold with **
    r'|(__[^_\n]+?__)'           # bold with __
    r'|(_[^_\n]+?_)',            # italics with _
    re.DOTALL
)


def _has_markdown_heading(text: str) -> bool:
    return bool(HEADING_PATTERN.search(text))


def _has_bullets_or_numbered_list(text: str) -> bool:
    return bool(BULLET_PATTERN.search(text) or NUMBERED_LIST_PATTERN.search(text))


def _has_emphasis(text: str) -> bool:
    return bool(EMPHASIS_PATTERN.search(text))


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - Clear headings
    - Bullet points or numbered list
    - Emphasized terms (bold or italics)

    Returns (is_valid, message).
    """
    if response is None or len(response.strip()) == 0:
        return (
            False,
            "The response is empty. Provide an answer with at least one Markdown element: heading, list, or emphasis."
        )

    has_heading = _has_markdown_heading(response)
    has_bullets = _has_bullets_or_numbered_list(response)
    has_emphasis = _has_emphasis(response)

    # OR logic: At least one element must be present
    has_any_formatting = has_heading or has_bullets or has_emphasis

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. A bulleted or numbered list (e.g., '- Item' or '1. Step')\n"
            "3. Bold or italic emphasis (e.g., **important** or *note*)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Collect information about what was found
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append("Consider adding a heading for structure.")

    if has_bullets:
        found_elements.append("list")
    else:
        suggestions.append("Consider adding a list for organization.")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("Consider using bold or italic for emphasis.")

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


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period '.'.
    Returns (is_valid, message).
    """
    if response is None or len(response.strip()) == 0:
        return (
            False,
            "The response is empty. Ensure the final visible character of the answer is a period '.'."
        )

    trimmed = response.rstrip()
    last_char = trimmed[-1] if trimmed else ""

    if last_char == ".":
        return (
            True,
            "Punctuation validated: the final visible character is a period."
        )

    hint = "Append a concluding sentence that ends with a period '.' after all sections and code fences."
    if trimmed.endswith("```"):
        hint += " The response currently ends with a code fence (```); add the final sentence after closing the code block."

    return (
        False,
        f"The final visible character is '{last_char}' rather than a period. {hint} Example: 'All dependencies were validated successfully.'."
    )

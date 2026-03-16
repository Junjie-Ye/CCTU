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
 Your response must include the exact phrase 'Royal announcement occurred on: ' immediately before the date in the final response. Additionally, you must ensure that the total number of tool calls made across all interaction turns does not exceed 2. The entire response must be formatted using Markdown syntax. Use proper Markdown elements like headings, bold, and lists if needed to enhance clarity.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '"Must include the exact phrase \'Royal announcement occurred on: \' immediately before the date in the final response."')
- idx 2: ('Response', 'Format', 'The entire response must be formatted using Markdown syntax. Use proper Markdown elements like headings, bold, and lists if needed to enhance clarity.')
"""

import re
from typing import Tuple

# Helper regex components
MONTHS = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
# Accept several common date formats:
# - 2024-05-17
# - 2024/05/17
# - March 4, 2021
# - 4 March 2021
DATE_PATTERN = rf"(?:\d{{4}}-\d{{2}}-\d{{2}}|\d{{4}}/\d{{2}}/\d{{2}}|{MONTHS}\s+\d{{1,2}},\s*\d{{4}}|\d{{1,2}}\s+{MONTHS}\s+\d{{4}})"

# Exact required phrase (note the trailing space)
REQUIRED_PHRASE = "Royal announcement occurred on: "

# Compiled regex to ensure the exact phrase is immediately followed by an optional bold marker and then a date
# Allows optional Markdown bold delimiters (** or __) around the date, with no other characters in between.
PHRASE_BEFORE_DATE_REGEX = re.compile(
    rf"{re.escape(REQUIRED_PHRASE)}(?P<bold>(\*\*|__))?{DATE_PATTERN}(?P=bold)?"
)

# Markdown detection helpers
HEADING_REGEX = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE)
BOLD_REGEX = re.compile(r"(\*\*|__)(?=\S)(.*?\S)\1",
                        re.DOTALL)  # **text** or __text__
LIST_REGEX = re.compile(r"^\s{0,3}(-|\*|\d+\.)\s+\S", re.MULTILINE)


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the exact phrase 'Royal announcement occurred on: '
    immediately before the date (with no intervening characters other than optional Markdown bold markers).
    """
    # 1) Must contain the exact phrase (including capitalization and trailing space)
    if REQUIRED_PHRASE not in response:
        return (
            False,
            "Missing required identifier phrase. Insert the exact phrase 'Royal announcement occurred on: ' "
            "with the same capitalization and the trailing space, immediately before the date line. "
            "Example: 'Royal announcement occurred on: 2024-05-17' or "
            "'Royal announcement occurred on: **March 4, 2021**'."
        )

    # 2) The phrase must be immediately followed by a recognizable date (optionally wrapped in ** or __)
    if not PHRASE_BEFORE_DATE_REGEX.search(response):
        return (
            False,
            "The exact phrase is present but is not immediately followed by a recognizable date. "
            "Place a valid date directly after 'Royal announcement occurred on: ' with no intervening text "
            "other than optional Markdown bold markers (** or __). Accepted date formats include: "
            "YYYY-MM-DD, YYYY/MM/DD, 'Month DD, YYYY', or 'DD Month YYYY'. "
            "Examples:\n"
            "- Royal announcement occurred on: 2023-11-01\n"
            "- Royal announcement occurred on: **March 4, 2021**\n"
            "Do not insert any other characters between the phrase and the date."
        )

    return (
        True,
        "Identifier check passed: the exact phrase appears immediately before a valid date."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements to enhance clarity:
      - A Markdown heading (#, ##, ..., ######)
      - A bold segment (**text** or __text__)
      - A list item (- item, * item, or 1. item)
    """
    has_heading = bool(HEADING_REGEX.search(response))
    has_bold = bool(BOLD_REGEX.search(response))
    has_list = bool(LIST_REGEX.search(response))

    # OR logic: At least one element must be present
    has_any_markdown = has_heading or has_bold or has_list

    if not has_any_markdown:
        return (
            False,
            "Your response is missing Markdown formatting. "
            "Include at least ONE of these elements to enhance clarity:\n\n"
            "Options:\n"
            "1. A Markdown heading (e.g., '# Title' or '## Section')\n"
            "2. Bold emphasis (e.g., '**Important:**')\n"
            "3. A list (e.g., '- item' or '1. step')\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Build feedback on what was found
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append(
            "Consider adding a heading for structure (e.g., '# Title').")

    if has_bold:
        found_elements.append("bold emphasis")
    else:
        suggestions.append(
            "Consider using bold for emphasis (e.g., '**Important:**').")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append(
            "Consider adding a list for organization (e.g., '- item').")

    # Build success message
    success_msg = f"Markdown format check passed: Found {', '.join(found_elements)}."

    if suggestions:
        success_msg += f" Suggestions: {' '.join(suggestions)}"

    return (True, success_msg)

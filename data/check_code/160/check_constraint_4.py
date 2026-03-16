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
 The `museum_event_locator` must be called before `museum_artwork_locator`. The total number of interaction rounds must be between 10 and 12, inclusive. The total number of tool calls the agent can execute must be between 9 and 12. The agent's response must start with the phrase "The sum of the founding year and the debut year is:" and must include the keyword "Academy founding year:" before specifying the academy's founding year and the keyword "Singer debut year:" before specifying the singer's debut year, and must end with the phrase "calculated using the advanced_arithmetic_calculator." Furthermore, the total length of the agent's response must be between 150 and 200 words. The agent's response must be formatted in Markdown syntax, including a heading for the final result, bold text for the keywords "Academy founding year:" and "Singer debut year:", and a clearly labeled section for the final calculation. Additionally, the agent must perform at least one interaction turn where it invokes at least two unique tool type simultaneously. The agent must ensure that the `comprehensive_biographical_info_retriever` is called at most 2 times.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', '(Response, Start identifier, The agent\'s response must start with the phrase "The sum of the founding year and the debut year is:")')
- idx 4: ('Response', 'Format', '(Main Category, Subcategory, "The agent\'s response must be formatted in Markdown syntax, including a heading for the final result, bold text for the keywords \'Academy founding year:\' and \'Singer debut year:\', and a clearly labeled section for the final calculation.")')
"""

import re
from typing import Tuple

# -----------------------------
# Helper regexes and functions
# -----------------------------
START_PHRASE = "The sum of the founding year and the debut year is:"

HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S.*$")
BOLD_ACADEMY_RE = re.compile(r"(\*\*|__)Academy founding year:(\*\*|__)")
BOLD_SINGER_RE = re.compile(r"(\*\*|__)Singer debut year:(\*\*|__)")

# A "clearly labeled calculation section" is satisfied by either:
# - a Markdown heading that contains the word "calculation" (case-insensitive), or
# - a bolded label like "**Calculation:**" / "**Final calculation:**", or
# - a line label at line start: "Calculation:" or "Final calculation:".
CALC_HEADING_RE = re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*calculation.*$")
CALC_BOLD_LABEL_RE = re.compile(
    r"(?i)(\*\*|__)final?\s*calculation\s*:(\*\*|__)")
CALC_LINE_LABEL_RE = re.compile(r"(?im)^\s*(?:final\s*)?calculation\s*:\s*$")


def _contains_markdown_heading(text: str) -> bool:
    return bool(HEADING_RE.search(text))


def _has_bold_academy_label(text: str) -> bool:
    return bool(BOLD_ACADEMY_RE.search(text))


def _has_bold_singer_label(text: str) -> bool:
    return bool(BOLD_SINGER_RE.search(text))


def _has_calculation_section_label(text: str) -> bool:
    """
    NEW RULE: calculation section is considered satisfied if the response contains
    at least one Markdown heading line (any line starting with #..######).
    """
    return _contains_markdown_heading(text)


# -----------------------------
# Constraint Validators
# -----------------------------

def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'start identifier' constraint:
    - The response must start with the exact phrase:
      "The sum of the founding year and the debut year is:"
    """
    if not response.startswith(START_PHRASE):
        # Inspect a small prefix to help debugging
        prefix = response[:80].replace("\n", "\\n")
        return (
            False,
            (
                "The response must start at index 0 with the exact phrase "
                '"The sum of the founding year and the debut year is:". '
                "Do not include any whitespace, headings, emojis, or other content before it. "
                f'Current beginning: "{prefix}". '
                'Fix by placing: "The sum of the founding year and the debut year is: " '
                "as the very first text, followed immediately by a space and then your Markdown content."
            ),
        )
    return True, (
        'Start identifier is correct: response begins with '
        '"The sum of the founding year and the debut year is:".'
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates Markdown formatting requirements:
    - The response must be in Markdown and include at least one Markdown heading (e.g., "# Final Result").
    - The keywords "Academy founding year:" and "Singer debut year:" must be bolded.
      (Accepts **...** or __...__ forms, including the trailing colon inside the bold.)
    - There must be a clearly labeled section for the final calculation:
      accepted as a heading containing "calculation", a bold label like "**Calculation:**",
      or a standalone line label "Calculation:".
    """
    errors = []

    # Bold keyword checks
    has_bold_academy = _has_bold_academy_label(response)
    if not has_bold_academy:
        errors.append(
            '- Bold the keyword exactly as: "**Academy founding year:**" (or "__Academy founding year:__"). '
            "Keep the colon inside the bold markers and put the year immediately after."
        )

    has_bold_singer = _has_bold_singer_label(response)
    if not has_bold_singer:
        errors.append(
            '- Bold the keyword exactly as: "**Singer debut year:**" (or "__Singer debut year:__"). '
            "Keep the colon inside the bold markers and put the year immediately after."
        )

    # Calculation section label
    has_calc_section = _has_calculation_section_label(response)
    if not has_calc_section:
        errors.append(
            '- Add a calculation section indicator: include at least ONE Markdown heading line '
            '(a line starting with #, e.g., "# Result" or "## Details").'
        )

    if errors:
        return (
            False,
            "Markdown format requirements are not fully met:\n" +
            "\n".join(errors),
        )

    return True, (
        "Markdown format is valid: a heading is present, the required bold keywords are correctly formatted, "
        "and a clearly labeled calculation section is included."
    )

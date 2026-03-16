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
 The answer must be formatted in Markdown, including bold text for the total number and bullet points listing the EU and UN language counts with their respective values. Additionally, the response must end with a period. The solution must be completed within at most 3 interaction turns with the toolset.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must be formatted in Markdown, including **bold text for the total number (e.g., **30**) and bullet points listing the EU and UN language counts with their respective values')
- idx 1: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period.)')
"""

import re
from typing import Tuple, List


# -----------------------------
# Helper utilities (shared)
# -----------------------------
BOLD_NUMBER_PATTERN = re.compile(r"\*\*\s*\d[\d,\s]*\s*\*\*")
BULLET_LINE_PATTERN = re.compile(r"^\s*[-*+]\s+")
INT_IN_LINE_PATTERN = re.compile(r"\d+")


def _extract_bullets(response: str) -> List[str]:
    """Return lines that are Markdown bullets (-, *, +)."""
    lines = response.splitlines()
    return [ln.strip() for ln in lines if BULLET_LINE_PATTERN.match(ln)]


def _has_bold_number(response: str) -> bool:
    """Check if there's at least one bolded numeric token like **30**."""
    return bool(BOLD_NUMBER_PATTERN.search(response))


def _line_has_label(line: str, label: str) -> bool:
    """Case-insensitive whole-word label check."""
    return re.search(rf"\b{re.escape(label)}\b", line, flags=re.IGNORECASE) is not None


def _line_has_integer(line: str) -> bool:
    """Check if a line contains at least one integer."""
    return bool(INT_IN_LINE_PATTERN.search(line))


# -----------------------------
# Validators
# -----------------------------
def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the 'format' constraint:
    - The answer must be formatted in Markdown.
    - Include bold text for the total combined number (e.g., **30**).
    - Include bullet points listing the EU and UN language counts with their respective values.
    """
    if not response or not response.strip():
        return (
            False,
            "The response is empty. Provide Markdown content that includes a bold total number "
            "(e.g., **30**) and two bullet items for EU and UN with numeric values."
        )

    issues: List[str] = []

    # 1) Bold total number check
    if not _has_bold_number(response):
        issues.append(
            "Missing bold total number. Include a bold numeric token such as '**30**' "
            "(for example: 'Total: **30**')."
        )

    # 2) Bullet points for EU and UN with numeric values
    bullets = _extract_bullets(response)
    if not bullets:
        issues.append(
            "Missing bullet list. Add two Markdown bullet lines (start with '-', '*' or '+'), "
            "one for EU and one for UN, each containing an integer value (e.g., '- EU: 24' and '- UN: 6')."
        )
    else:
        eu_bullets = [b for b in bullets if _line_has_label(b, "EU")]
        un_bullets = [b for b in bullets if _line_has_label(b, "UN")]

        if not eu_bullets:
            issues.append(
                "No bullet item found for 'EU'. Add a bullet line like '- EU: 24'."
            )
        else:
            if not any(_line_has_integer(b) for b in eu_bullets):
                issues.append(
                    "The 'EU' bullet does not include a numeric value. Include an integer, e.g., '- EU: 24'."
                )

        if not un_bullets:
            issues.append(
                "No bullet item found for 'UN'. Add a bullet line like '- UN: 6'."
            )
        else:
            if not any(_line_has_integer(b) for b in un_bullets):
                issues.append(
                    "The 'UN' bullet does not include a numeric value. Include an integer, e.g., '- UN: 6'."
                )

    if issues:
        return (
            False,
            "Format requirements not met: "
            + " ".join(issues)
            + " Ensure the answer is in Markdown, includes a bold total number, and has two bullet items "
              "for EU and UN with their integer values."
        )

    return True, "Format is valid: bold total number found and bullet items for EU and UN with numeric values are present."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate the 'punctuation' constraint:
    - The response must end with a period '.'.
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty. Provide the answer and ensure the final character is a period '.'."
        )

    trimmed = response.rstrip()
    if not trimmed.endswith("."):
        return (
            False,
            "The response must end with a period '.'. Ensure the very last character of the entire output "
            "is '.'. If your last line is a bullet item, you can place the period at the end of that line "
            "or add a brief closing line that ends with '.'. Avoid trailing characters (e.g., ')', '\"', or code fences) after the period."
        )

    return True, "Ending punctuation is valid: the response ends with a period."

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
 The answer must be at least 150 characters to ensure sufficient detail, including both wingspan measurements and the difference. **If the agent intends to retrieve the specifications for both aircraft models**, the **aircraft_specifications_retriever** tool must be invoked twice **in a single parallel action**. Additionally, the agent must execute at least one interaction turn where it invokes at least two tool calls simultaneously during the task. The response must explicitly separate the wingspan values and the difference using bold formatting (**...**) to highlight the numerical values and the result, ensuring the keywords 'wingspan', 'difference', and 'centimeters' are included in their respective sections. The entire response must be formatted using Markdown syntax, with proper use of headings, lists, and bold/italic text to enhance readability. Importantly, the **aircraft_specifications_retriever** tool must not be invoked more than 2 times in total during the task.

response_constraints_non_length:
- idx 3: ('Response', 'Identifiers', '(Response, Delimiting identifier, "Must include the keywords \'wingspan\', \'difference\', and \'centimeters\' within designated sections marked by bold formatting (**...**) to separate the numerical values and the result.")')
- idx 5: ('Response', 'Format', '(Response, Format, "Markdown (Mandates that the agent\'s entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")')
"""

import re
from typing import Tuple, List

# ----------------------------
# Helper utilities
# ----------------------------

BOLD_SEGMENT_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE)
LIST_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*]\s+|\d+[.)]\s+)\S", re.MULTILINE)


def _extract_bold_segments(response: str) -> List[str]:
    """
    Return a list of text segments that are wrapped in bold Markdown (**...**).
    """
    return [m.strip() for m in BOLD_SEGMENT_RE.findall(response or "")]


def _has_heading(response: str) -> bool:
    """
    Detect if there is at least one Markdown heading line starting with #.
    """
    return bool(HEADING_RE.search(response or ""))


def _count_list_items(response: str) -> int:
    """
    Count Markdown list items (bulleted or numbered).
    """
    return len(LIST_ITEM_RE.findall(response or ""))


def _has_any_bold(response: str) -> bool:
    """
    Check if there is at least one bold segment (**...**).
    """
    return bool(BOLD_SEGMENT_RE.search(response or ""))


def _contains_keyword_in_bold(response: str, keyword: str) -> bool:
    """
    Check if at least one bold segment contains the given keyword (case-insensitive).
    """
    keyword_l = keyword.lower()
    for seg in _extract_bold_segments(response):
        if keyword_l in seg.lower():
            return True
    return False


# ----------------------------
# Validators
# ----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (# ...)
    - A list (bulleted '-' or '*' or ordered '1.' / '1)') with at least one items
    - Bold emphasis (**...**) for keywords and numbers
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Include at least one Markdown element: heading, list, or bold emphasis."
        )

    errors = []
    suggestions = []
    found_elements = []

    # Check each element
    has_heading = _has_heading(response)
    list_count = _count_list_items(response)
    has_list = list_count >= 1  # List must have at least 3 items
    has_bold = _has_any_bold(response)

    # OR logic: At least one element must be present
    has_any_formatting = has_heading or has_list or has_bold

    if not has_any_formatting:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Results')\n"
            "2. A list with at least 3 items (e.g., '- Item 1', '- Item 2', '- Item 3')\n"
            "3. Bold emphasis for keywords/numbers (e.g., **important** or **123**)\n\n"
            "Example minimal format: '# Comparison' (just a heading is sufficient)"
        )

    # Record what was found and provide suggestions
    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append(
            "- Add a heading like: '# Wingspan Comparison' or '## Final Results'.")

    if has_list:
        found_elements.append(f"list with {list_count} items")
    else:
        suggestions.append("- Add a list with at least 3 items.")

    if has_bold:
        found_elements.append("bold emphasis")
    else:
        suggestions.append(
            "- Add bold emphasis for keywords and numbers using **...**.")

    # Build response message
    if found_elements:
        success_msg = f"Format acceptable: Found {', '.join(found_elements)}."
        if suggestions:
            success_msg += "\n\nSuggestions for improvement:\n" + \
                "\n".join(suggestions)
        return True, success_msg
    else:
        # This should not happen due to has_any_formatting check, but just in case
        return True, "Format minimal: At least one condition met."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that required keywords appear in bold (**...**) as identifiers in the designated sections:
    - 'wingspan' must appear inside a bold segment: **wingspan**
    - 'difference' must appear inside a bold segment: **difference**
    - 'centimeters' must appear inside a bold segment: **centimeters**
    """
    required_keywords = ["wingspan", "difference", "centimeters"]
    missing = [
        kw for kw in required_keywords if not _contains_keyword_in_bold(response, kw)]

    if missing:
        tips = []
        if "wingspan" in missing:
            tips.append(
                "- Wrap the keyword 'wingspan' in bold wherever you state each aircraft measurement, "
                "e.g., '- **wingspan** of Boeing 787-9: **60400** **centimeters**'."
            )
        if "difference" in missing:
            tips.append(
                "- Wrap the keyword 'difference' in bold in the result line, "
                "e.g., '- **difference**: **4500** **centimeters**'."
            )
        if "centimeters" in missing:
            tips.append(
                "- Wrap the unit 'centimeters' in bold anywhere you present numeric values, "
                "e.g., '**centimeters**'."
            )

        example = (
            "Example snippet:\n"
            "- **wingspan** of Boeing 787-9: **60400** **centimeters**\n"
            "- **wingspan** of Airbus A350-900: **64900** **centimeters**\n"
            "- **difference**: **4500** **centimeters**"
        )

        message = (
            "Required bold identifiers are missing: "
            + ", ".join(f"'{kw}'" for kw in missing)
            + ". Each keyword must appear inside **...** to clearly mark the sections and separate values.\n"
            + "\n".join(tips)
            + "\n" + example
        )
        return False, message

    return True, "All required identifiers ('wingspan', 'difference', 'centimeters') appear within bold (**...**) segments."

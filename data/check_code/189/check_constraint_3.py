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
 The response must include the exact phrases "The area of the national reserve is **[value]** [unit]" and "The book has **[value]** pages" to clearly separate the two values, followed by the final answer in bold using the format "**Answer:** (a)/(b)". The response must be formatted in Markdown syntax, including proper use of bold formatting, headings, and paragraph structure to ensure clarity and visual appeal. You must include at least one interaction turn where you invoke at least 2 unique tools simultaneously. Additionally, the total number of interaction turns must be in the range of 5 to 10 (inclusive), the total number of tool calls must be in the range of 6 to 8 (inclusive), and the response must end with a period to ensure proper sentence closure. If the agent intends to invoke the 'historical_experiment_locator' tool**, the 'historical_invention_info' tool must be executed beforehand.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', 'The response must include the exact phrases "The area of the national reserve is **[value]** [unit]" and "The book has **[value]** pages" to clearly separate the two values, followed by the final answer in bold using the format "**Answer:** (a)/(b)".')
- idx 3: ('Response', 'Punctuation', '(Response, Ending punctuation, The response must end with a period to ensure proper sentence closure.)')
- idx 7: ('Response', 'Format', '(Response, Format, The response must be formatted in Markdown syntax, including proper use of bold formatting, headings, and paragraph structure to ensure clarity and visual appeal)')
"""

import re
from typing import Tuple, List

# ---------- Shared helpers and compiled regexes ----------
AREA_PATTERN = re.compile(
    r'The area of the national reserve is\s+'
    r'(?:\*\*(?P<value_bold>[^*]+?)\*\*|(?P<value_plain>\S+))\s+'
    r'(?P<unit>[A-Za-z0-9μμ^/.\-\s]+?)'
    r'(?=[\s]*[.,;!?)]|$)'
)

PAGES_PATTERN = re.compile(
    r'The book has\s+'
    r'(?:\*\*(?P<pages_bold>[^*]+?)\*\*|(?P<pages_plain>\S+))\s+'
    r'pages(?=[\s]*[.,;!?)]|$)'
)

FINAL_ANSWER_PATTERN = re.compile(
    r'\*\*Answer:\*\*\s*\(a\)\s*/\s*\(b\)'
)

AREA_NEAR = re.compile(r'The area of the national reserve is\b')
PAGES_NEAR = re.compile(r'The book has\b')
ANSWER_NEAR = re.compile(r'\*\*Answer:\*\*')

HEADING_PATTERN = re.compile(r'(?m)^\#{1,6}\s+\S')
BOLD_PATTERN = re.compile(r'\*\*[^*]+\*\*')


def _last_non_ws_char(s: str) -> str:
    i = len(s) - 1
    while i >= 0 and s[i].isspace():
        i -= 1
    return s[i] if i >= 0 else ''


def _paragraph_blocks(s: str) -> List[str]:
    # Paragraphs are blank-line separated blocks
    return [blk for blk in re.split(r'\n\s*\n', s.strip()) if blk.strip()]


def _pick(m: re.Match, a: str, b: str) -> str:
    return (m.group(a) or m.group(b) or "").strip()


def _looks_like_unreplaced_placeholder(s: str) -> bool:
    return ("[" in s) or ("]" in s)


# ---------- Validators ----------

def validate_identifiers(response: str) -> Tuple[bool, str]:
    errors: List[str] = []
    guidance: List[str] = []

    area_m = AREA_PATTERN.search(response)
    pages_m = PAGES_PATTERN.search(response)
    final_m = FINAL_ANSWER_PATTERN.search(response)

    # ---- Area phrase ----
    if not area_m:
        if AREA_NEAR.search(response):
            errors.append(
                "Area sentence is present but does not match the required phrase shape.")
            guidance.append(
                "Use this exact shape:\n"
                "The area of the national reserve is <value> <unit>\n"
                "Example: The area of the national reserve is 123 km2"
            )
        else:
            errors.append(
                'Missing required phrase: The area of the national reserve is [value] [unit].')
            guidance.append(
                "Add a sentence that contains: The area of the national reserve is <value> <unit>")
    else:
        area_value = _pick(area_m, "value_bold", "value_plain")
        area_unit = (area_m.group("unit") or "").strip()

        if not area_value or _looks_like_unreplaced_placeholder(area_value):
            errors.append(
                "Area value is missing or still a placeholder like [value].")
            guidance.append(
                "Replace [value] with an actual value (bold is optional).")

        if not area_unit or _looks_like_unreplaced_placeholder(area_unit):
            errors.append(
                "Area unit is missing or still a placeholder like [unit].")
            guidance.append(
                "Replace [unit] with an actual unit (e.g., km2, hectares, ha).")

    # ---- Pages phrase ----
    if not pages_m:
        if PAGES_NEAR.search(response):
            errors.append(
                "Pages sentence is present but does not match the required phrase shape.")
            guidance.append(
                "Use this exact shape:\n"
                "The book has <value> pages\n"
                "Example: The book has 432 pages"
            )
        else:
            errors.append(
                'Missing required phrase: The book has [value] pages.')
            guidance.append(
                "Add a sentence that contains: The book has <value> pages")
    else:
        pages_value = _pick(pages_m, "pages_bold", "pages_plain")
        if not pages_value or _looks_like_unreplaced_placeholder(pages_value):
            errors.append(
                "Page value is missing or still a placeholder like [value].")
            guidance.append(
                "Replace [value] with an actual page count (bold is optional).")

    # ---- Final Answer phrase ----
    if not final_m:
        if ANSWER_NEAR.search(response):
            errors.append(
                "Answer line is present but does not match the exact required literal '**Answer:** (a)/(b)'.")
            guidance.append("Use exactly: **Answer:** (a)/(b)")
        else:
            errors.append("Missing required phrase: **Answer:** (a)/(b).")
            guidance.append("Add the literal phrase: **Answer:** (a)/(b)")

    # ---- Ordering (keep or remove) ----
    if area_m and pages_m and final_m:
        final_pos = final_m.start()
        if not (final_pos > area_m.start() and final_pos > pages_m.start()):
            errors.append(
                "The '**Answer:** (a)/(b)' phrase must appear after the area and pages phrases.")
            guidance.append(
                "Move '**Answer:** (a)/(b)' to after the two required sentences.")

    if errors:
        message = (
            "Identifier constraints failed:\n- "
            + "\n- ".join(errors)
            + "\n\nHow to fix:\n- "
            + "\n- ".join(guidance)
        )
        return False, message

    return True, "Identifiers OK: all required phrases are present with non-placeholder values, and Answer is exact."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the response ends with a period, after trimming trailing whitespace.
    """
    last_char = _last_non_ws_char(response)
    if last_char != '.':
        return (
            False,
            "Ending punctuation constraint failed: the response must end with a period '.'. "
            "Add a final period at the very end of the response."
        )
    return True, "Ending punctuation constraint satisfied: the response ends with a period."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates that the response contains at least ONE of these formatting elements:
    - A Markdown heading (# ... or ## ... etc.)
    - Bold formatting (e.g., **text**)
    - Paragraph structure (at least two blank-line-separated blocks)
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Include at least one formatting element: heading, bold text, or paragraph structure."
        )

    has_heading = bool(HEADING_PATTERN.search(response))
    has_bold = bool(BOLD_PATTERN.search(response))
    paragraphs = _paragraph_blocks(response)
    has_paragraph_structure = len(paragraphs) >= 2

    has_any_formatting = has_heading or has_bold or has_paragraph_structure
    if not has_any_formatting:
        return (
            False,
            "Missing formatting elements. Include at least ONE of these:\n"
            "1) A Markdown heading (e.g., '# Title')\n"
            "2) Bold formatting (e.g., **important**)\n"
            "3) At least 2 paragraphs separated by a blank line"
        )

    found = []
    if has_heading:
        found.append("heading")
    if has_bold:
        found.append("bold")
    if has_paragraph_structure:
        found.append("paragraphs")

    return True, f"Format OK: found {', '.join(found)}."

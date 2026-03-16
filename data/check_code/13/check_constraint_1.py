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
 The response must end with a period to ensure proper sentence closure and must contain a table with a single row and column to clearly present the date, ensuring proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
- idx 1: ('Response', 'Format', '(Response, Format, The response must contain a table with a single row and column to clearly present the date, ensuring proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information.)')
"""

import re
from typing import Tuple, List, Optional


# ----------------------------
# Helper utilities
# ----------------------------

MONTHS_SHORT = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]
MONTHS_LONG = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

DATE_PATTERNS = [
    # ISO formats
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),
    # US style: Month DD, YYYY
    re.compile(
        r"^(?:" + "|".join(MONTHS_SHORT + MONTHS_LONG) +
        r")\s+\d{1,2},\s+\d{4}$",
        re.IGNORECASE
    ),
    # European style: DD Month YYYY
    re.compile(
        r"^\d{1,2}\s+(?:" + "|".join(MONTHS_SHORT +
                                     MONTHS_LONG) + r")\s+\d{4}$",
        re.IGNORECASE
    ),
    # Numeric US style: MM/DD/YYYY
    re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"),
    # Numeric EU style: DD/MM/YYYY
    re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"),
]


def is_date_string(text: str) -> bool:
    """
    Return True if text looks like a valid date string in common formats.
    """
    s = text.strip()
    for pat in DATE_PATTERNS:
        if pat.match(s):
            return True
    return False


def strip_html_tags(html: str) -> str:
    """
    Remove HTML tags to get text content.
    """
    return re.sub(r"<[^>]+>", "", html, flags=re.DOTALL).strip()


def _split_md_cells(line: str) -> List[str]:
    """
    Split a Markdown table row into cell texts, handling optional leading/trailing pipes.
    """
    raw = line.strip()
    if "|" not in raw:
        return []
    parts = raw.split("|")
    # Remove empty leading/trailing cells created by edge pipes
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def _is_md_separator_cell(cell: str) -> Tuple[bool, bool]:
    """
    Check if a cell is a Markdown separator (--- with optional colons).
    Returns (is_separator, has_alignment).
    """
    c = cell.strip()
    # Must be hyphens with optional colon at start or end, at least 3 hyphens
    m = re.match(r"^:?-{3,}:?\s*$", c)
    if not m:
        return False, False
    # Alignment is indicated by colon either at start or end (or both)
    has_alignment = c.startswith(":") or c.endswith(":")
    return True, has_alignment


def _find_markdown_table(response: str) -> Optional[dict]:
    """
    Find a single-column Markdown table with header/separator/data rows.
    Returns a dict with details if found, else None.
    Also enforces exactly one data row for the table.
    """
    lines = response.splitlines()
    for i in range(len(lines) - 2):
        header_cells = _split_md_cells(lines[i])
        sep_cells = _split_md_cells(lines[i + 1])
        data_cells = _split_md_cells(lines[i + 2])

        # Validate structure
        if not header_cells or not sep_cells or not data_cells:
            continue

        # Require single-column table
        if not (len(header_cells) == len(sep_cells) == len(data_cells) == 1):
            continue

        # Separator cell must be valid and include alignment
        is_sep, has_align = _is_md_separator_cell(sep_cells[0])
        if not is_sep or not has_align:
            continue

        header_text = header_cells[0].strip()
        data_text = data_cells[0].strip()

        # Ensure the next line is not another data row of the same table (single data row only)
        has_extra_row = False
        if i + 3 < len(lines):
            next_cells = _split_md_cells(lines[i + 3])
            if next_cells and len(next_cells) == 1:
                # This looks like another table row, so more than one data row
                has_extra_row = True

        return {
            "header_text": header_text,
            "data_text": data_text,
            "has_alignment": has_align,
            "single_column": True,
            "single_data_row": not has_extra_row,
            "start_index": i,
        }
    return None


def _find_html_table(response: str) -> Optional[dict]:
    """
    Find a single-column HTML table with one header cell and one data cell.
    Requires explicit alignment via style='text-align:...' or align='...'.
    Requires exactly one tbody row with one td.
    """
    for m in re.finditer(r"<table\b[^>]*>(.*?)</table>", response, flags=re.IGNORECASE | re.DOTALL):
        tbl = m.group(0)
        tbl_inner = m.group(1)

        # Extract header cells (prefer thead, but accept any th)
        thead_match = re.search(
            r"<thead\b[^>]*>(.*?)</thead>", tbl_inner, flags=re.IGNORECASE | re.DOTALL)
        if thead_match:
            thead_content = thead_match.group(1)
            ths = re.findall(
                r"<th\b[^>]*>(.*?)</th>", thead_content, flags=re.IGNORECASE | re.DOTALL)
        else:
            ths = re.findall(r"<th\b[^>]*>(.*?)</th>",
                             tbl_inner, flags=re.IGNORECASE | re.DOTALL)

        # Extract body rows
        tbody_match = re.search(
            r"<tbody\b[^>]*>(.*?)</tbody>", tbl_inner, flags=re.IGNORECASE | re.DOTALL)
        if not tbody_match:
            # If no tbody, treat as failure for clarity of structure
            continue
        tbody_content = tbody_match.group(1)

        trs = re.findall(r"<tr\b[^>]*>(.*?)</tr>",
                         tbody_content, flags=re.IGNORECASE | re.DOTALL)
        if len(ths) != 1 or len(trs) != 1:
            # Must have one header cell and exactly one data row
            continue

        # Extract data cells from the single row
        tds = re.findall(r"<td\b[^>]*>(.*?)</td>",
                         trs[0], flags=re.IGNORECASE | re.DOTALL)
        if len(tds) != 1:
            continue

        header_text = strip_html_tags(ths[0])
        data_text = strip_html_tags(tds[0])

        # Check explicit alignment (on table, th, or td)
        align_present = False
        align_regex = re.compile(
            r'(?:style="[^"]*text-align\s*:\s*(left|center|right)[^"]*"|align="(left|center|right)")', re.IGNORECASE)
        if align_regex.search(tbl) or align_regex.search(ths[0]) or align_regex.search(tds[0]):
            align_present = True

        return {
            "header_text": header_text,
            "data_text": data_text,
            "has_alignment": align_present,
            "single_column": True,
            "single_data_row": True,
        }

    return None


# ----------------------------
# Validators
# ----------------------------

def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final non-whitespace character of the response is a period '.'.
    """
    if not response.strip():
        return (
            False,
            "The response is empty. Provide the final answer and ensure the last non-whitespace character is a period '.' at the end."
        )
    trimmed = response.rstrip()
    if not trimmed.endswith("."):
        return (
            False,
            "The response must end with a period. Append a single '.' as the final character of the entire response (after the table and any text), with no trailing characters or whitespace after it."
        )
    return (
        True,
        "Punctuation is correct: the response ends with a period."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a table with a single row and single column,
    uses a header to label the date, includes explicit alignment, and presents a recognizable date value.
    Accepts either a Markdown table or an HTML table.
    """
    md_tbl = _find_markdown_table(response)
    html_tbl = _find_html_table(response)

    # Prefer validating whichever valid structure is present
    candidate = md_tbl if md_tbl else html_tbl

    if candidate is None:
        return (
            False,
            "No valid table detected. Your final answer must contain exactly one table with a single column and a single data row that presents the date. "
            "Requirements: (1) Include a header cell labeled 'Date'. (2) Ensure explicit alignment is set (Markdown: use colons in the separator row, e.g., '|:---:|' for centered; HTML: use style='text-align:...' or align='...'). "
            "(3) The body must have exactly one row with one cell containing only the date in a standard format (e.g., 'YYYY-MM-DD', 'Month DD, YYYY', 'DD Month YYYY', or 'MM/DD/YYYY'). "
            "Markdown example shape (description): header row with one cell 'Date', a separator row like ':---:' to set alignment, and exactly one data row containing the date. "
            "HTML example shape (description): <table> with a <thead><tr><th>Date</th></tr></thead> and a <tbody><tr><td>YYYY-MM-DD</td></tr></tbody>, with text-align specified. "
            "Place the table in the final answer and ensure there are no additional rows or columns beyond the single data cell."
        )

    # Validate common requirements
    header_ok = bool(
        re.search(r"\bdate\b", candidate["header_text"], flags=re.IGNORECASE))
    date_ok = is_date_string(candidate["data_text"])
    align_ok = bool(candidate["has_alignment"])
    single_col_ok = bool(candidate["single_column"])
    single_row_ok = bool(candidate["single_data_row"])

    if header_ok and date_ok and align_ok and single_col_ok and single_row_ok:
        return (
            True,
            "Format is correct: a single-column table with a 'Date' header, explicit alignment, and exactly one data row containing a recognizable date was found."
        )

    # Build failure message with precise guidance
    issues = []
    if not header_ok:
        issues.append(
            "The header cell must contain the word 'Date' (case-insensitive).")
    if not date_ok:
        issues.append(
            "The single data cell must contain only a date in a standard format such as 'YYYY-MM-DD', 'Month DD, YYYY', 'DD Month YYYY', or 'MM/DD/YYYY'.")
    if not align_ok:
        issues.append("Explicit alignment is required. For Markdown, use colons in the separator row (e.g., '|:---:|'). For HTML, set text-align via style='text-align:center' or align='center' on the <table>, <th>, or <td>.")
    if not single_col_ok:
        issues.append("The table must have exactly one column.")
    if not single_row_ok:
        issues.append("The table must have exactly one data row.")

    return (
        False,
        "The table format is not compliant. Please fix the following: "
        + " ".join(issues) + " "
        + "Ensure the final answer contains exactly one such table and ends with a period."
    )

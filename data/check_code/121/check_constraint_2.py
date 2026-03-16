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
 You must use the provided tools to retrieve the information. The total number of tool calls must not exceed 2. The 'historical_event_information_tool' must be limited to a single call. If the agent intends to invoke the 'historical_event_information_tool' for multiple events, it must be executed in a single action step. Complete the task within a total of 3 to 5 interaction rounds and present your final answer in a tabular format with columns for the event names, locations, casualty numbers, and the difference in casualties.

response_constraints_non_length:
- idx 2: ('Response', 'Format', '(Response, Table, The final answer must be presented in a tabular format, with columns for the event names, locations, casualty numbers, and the difference in casualties.)')
"""

import re
from typing import List, Tuple, Optional

# ----------------------------
# Helpers for parsing and normalization
# ----------------------------

REQUIRED_COLUMNS = [
    "Event Name",
    "Location",
    "Casualty Numbers",
    "Difference in Casualties",
]


def _normalize_header_cell(text: str) -> str:
    """
    Normalize a header cell for comparison:
    - strip markdown emphasis/backticks
    - collapse spaces
    - lowercase
    """
    if text is None:
        return ""
    # remove common markdown decorators
    s = re.sub(r'[`_*~]', '', text)
    # remove surrounding pipes accidentally kept
    s = s.strip().strip('|').strip()
    # collapse whitespace to single space
    s = re.sub(r'\s+', ' ', s)
    return s.lower()


def _normalize_headers(headers: List[str]) -> List[str]:
    return [_normalize_header_cell(h) for h in headers]


def _required_columns_normalized() -> List[str]:
    return [_normalize_header_cell(c) for c in REQUIRED_COLUMNS]


def _is_markdown_separator(line: str) -> bool:
    """
    Detect a Markdown table header separator line like:
    | --- | :---: | ---: |
    Also allow without leading/trailing pipes.
    """
    if not line:
        return False
    s = line.strip()
    pattern = r'^(\|\s*)?:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+(\|\s*)?$'
    return re.match(pattern, s) is not None


def _split_pipe_row(line: str) -> List[str]:
    """
    Split a Markdown/pipe-delimited table row into cells.
    Handles leading/trailing pipes.
    """
    # Remove leading/trailing pipe if present
    trimmed = line.strip()
    if trimmed.startswith('|'):
        trimmed = trimmed[1:]
    if trimmed.endswith('|'):
        trimmed = trimmed[:-1]
    # Split by '|' and strip each cell
    cells = [c.strip() for c in trimmed.split('|')]
    return cells


def _extract_markdown_tables(text: str) -> List[Tuple[List[str], List[List[str]]]]:
    """
    Extract Markdown-style tables.
    Returns a list of (headers, rows).
    """
    lines = text.splitlines()
    tables: List[Tuple[List[str], List[List[str]]]] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Heuristic: candidate header if it contains at least one pipe and splits into >= 2 cells
        if '|' in line and len(_split_pipe_row(line)) >= 2:
            # Look ahead for a separator within the next 2 non-empty lines
            j = i + 1
            while j < n and lines[j].strip() == '':
                j += 1
            if j < n and _is_markdown_separator(lines[j]):
                header_cells = _split_pipe_row(line)
                # Gather data rows until a blank line or a non-table line encountered
                rows: List[List[str]] = []
                k = j + 1
                while k < n and lines[k].strip() != '':
                    if '|' in lines[k]:
                        row_cells = _split_pipe_row(lines[k])
                        # Skip lines that look like another separator (defensive)
                        if not _is_markdown_separator(lines[k]):
                            rows.append(row_cells)
                        k += 1
                    else:
                        break
                tables.append((header_cells, rows))
                i = k
                continue
        i += 1
    return tables


def _strip_html_tags(s: str) -> str:
    return re.sub(r'<[^>]+>', '', s or '').strip()


def _extract_html_tables(text: str) -> List[Tuple[List[str], List[List[str]]]]:
    """
    Very lightweight HTML table extractor using regex (no external deps).
    Returns a list of (headers, rows).
    """
    tables: List[Tuple[List[str], List[List[str]]]] = []
    for tbl_match in re.finditer(r'<table\b[^>]*>(.*?)</table>', text, flags=re.I | re.S):
        tbl_html = tbl_match.group(1)
        # Extract header cells from <th>; if none, use first row's <td>
        headers: List[str] = []
        ths = re.findall(r'<th\b[^>]*>(.*?)</th>', tbl_html, flags=re.I | re.S)
        if ths:
            headers = [_strip_html_tags(h) for h in ths]
        else:
            # Fallback: first tr's tds
            first_tr = re.search(
                r'<tr\b[^>]*>(.*?)</tr>', tbl_html, flags=re.I | re.S)
            if first_tr:
                headers = [_strip_html_tags(td) for td in re.findall(
                    r'<t[dh]\b[^>]*>(.*?)</t[dh]>', first_tr.group(1), flags=re.I | re.S)]
        # Extract data rows from subsequent <tr>
        rows: List[List[str]] = []
        for tr_match in re.finditer(r'<tr\b[^>]*>(.*?)</tr>', tbl_html, flags=re.I | re.S):
            tr_html = tr_match.group(1)
            cells = re.findall(
                r'<t[dh]\b[^>]*>(.*?)</t[dh]>', tr_html, flags=re.I | re.S)
            cells_clean = [_strip_html_tags(c) for c in cells]
            # Skip if this row equals the header (common when no <th>)
            if cells_clean and cells_clean != headers:
                rows.append(cells_clean)
        if headers:
            # Remove potential duplication where header row got included as data
            if rows and rows[0] == headers:
                rows = rows[1:]
            tables.append((headers, rows))
    return tables


def _find_best_table_match(tables: List[Tuple[List[str], List[List[str]]]]) -> Tuple[Optional[int], str]:
    """
    Among provided tables, find the index that best matches the required header.
    Returns (index, reason_if_no_exact_match).
    """
    required_norm = _required_columns_normalized()
    best_idx = None
    best_score = -1
    best_reason = "No table with the required columns was found."
    for idx, (headers, rows) in enumerate(tables):
        headers_norm = _normalize_headers(headers)
        # Score by how many required columns are present in correct order
        # Exact match and exact order gets top score
        if headers_norm == required_norm:
            return idx, ""  # perfect match
        # Partial scoring: number of required columns present (order-agnostic)
        overlap = sum(1 for h in headers_norm if h in set(required_norm))
        score = overlap
        if score > best_score:
            best_score = score
            # Build a detailed reason for this table
            missing = [c for c in required_norm if c not in headers_norm]
            extra = [h for h in headers_norm if h not in required_norm]
            reason_parts = []
            if missing:
                reason_parts.append(f"Missing columns: {', '.join(missing)}.")
            if extra:
                reason_parts.append(f"Unexpected columns: {', '.join(extra)}.")
            # Order hint
            if sorted(headers_norm) == sorted(required_norm) and headers_norm != required_norm:
                reason_parts.append("Columns present but in the wrong order.")
            best_reason = " ".join(
                reason_parts) if reason_parts else best_reason
            best_idx = idx
    return best_idx, best_reason

# ----------------------------
# Validator for "format"
# ----------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer is presented in a tabular format
    with columns: Event Name, Location, Casualty Numbers, Difference in Casualties.
    Accepts Markdown or HTML tables. Requires at least one data row.
    Returns (is_valid, detailed_feedback_in_english).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a Markdown or HTML table with the exact columns: "
            "'Event Name', 'Location', 'Casualty Numbers', and 'Difference in Casualties', followed by at least one data row."
        )

    # Extract tables (Markdown first, then HTML)
    md_tables = _extract_markdown_tables(response)
    html_tables = _extract_html_tables(response)
    all_tables = md_tables + html_tables

    if not all_tables:
        return (
            False,
            "No table was detected. Present the final answer as a table. Example Markdown structure:\n"
            "| Event Name | Location | Casualty Numbers | Difference in Casualties |\n"
            "| --- | --- | --- | --- |\n"
            "| Kemi Bloody Thursday | Kemi, Finland | 2 | 5 |\n"
            "Ensure there is at least one data row and do not include extra columns or narrative text before the table."
        )

    # Find the best matching table by headers
    idx, reason = _find_best_table_match(all_tables)
    if idx is None:
        # Provide guidance using the best found reason
        return (
            False,
            f"A table was found but the headers do not match the required set. {reason} "
            "Use exactly these headers (in this order): 'Event Name', 'Location', 'Casualty Numbers', 'Difference in Casualties'. "
            "Include at least one data row. Avoid extra columns or alternative header names."
        )

    headers, rows = all_tables[idx]
    # Verify exact normalized header order
    if _normalize_headers(headers) != _required_columns_normalized():
        missing = [c for c in _required_columns_normalized(
        ) if c not in _normalize_headers(headers)]
        extra = [h for h in _normalize_headers(
            headers) if h not in _required_columns_normalized()]
        order_note = ""
        if sorted(_normalize_headers(headers)) == sorted(_required_columns_normalized()):
            order_note = " The required columns are present but not in the correct order."
        return (
            False,
            "The detected table does not have the exact required headers in the correct order. "
            f"Missing: {', '.join(missing) if missing else 'None'}. Unexpected: {', '.join(extra) if extra else 'None'}.{order_note} "
            "Rewrite the header row exactly as: | Event Name | Location | Casualty Numbers | Difference in Casualties |"
        )

    # Require at least one data row
    # Filter out rows that are entirely empty after stripping
    nonempty_rows = []
    for r in rows:
        # Pad/truncate to 4 cells to judge emptiness robustly
        cells = (r + [""] * 4)[:4]
        if any(str(c).strip() for c in cells):
            nonempty_rows.append(cells)

    if len(nonempty_rows) < 1:
        return (
            False,
            "The table has no data rows. Add at least one row with values for all four columns. "
            "Example: | Kemi Bloody Thursday | Kemi, Finland | 2 | 5 |"
        )

    # If we reach here, format is correct
    return (
        True,
        "The response satisfies the format requirement: a table with the exact headers "
        "'Event Name', 'Location', 'Casualty Numbers', and 'Difference in Casualties' and at least one data row."
    )

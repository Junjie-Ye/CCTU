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
 The AI Agent must perform at least one interaction turn where it invokes at least one unique tool type simultaneously. If the agent intends to invoke the `historical_event_info_retriever` tool, it must be executed twice within a single action step. The agent must not call the `historical_event_info_retriever` tool more than twice in total during the task, and the total number of tool calls across all interaction turns must not exceed 3. The final answer must be presented in a tabular format with at least two columns: one for event names and one for casualty numbers, and a third column explicitly showing the calculated difference between the two values.

response_constraints_non_length:
- idx 4: ('Response', 'Format', '(Response, Table, The final answer must be presented in a tabular format with at least two columns: one for event names and one for casualty numbers, and a third column explicitly showing the calculated difference between the two values)')
"""

import re
from typing import Tuple, List, Optional


# ---------------------------
# Helper functions for parsing
# ---------------------------

def _strip_html_tags(text: str) -> str:
    """Remove HTML tags."""
    return re.sub(r"(?is)<[^>]+>", "", text).strip()


def _is_numeric_cell(s: str) -> bool:
    """
    Check if a string represents a numeric value (int or float), allowing thousands separators.
    Examples: '123', '1,234', '-2,345.67'
    """
    s = s.strip()
    if not s:
        return False
    # Accept numbers with optional commas and decimal point
    return bool(re.fullmatch(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?", s))


def _is_textual_event_name(s: str) -> bool:
    """
    Check that the cell looks like an event name (contains letters and not purely numeric).
    """
    s = s.strip()
    if not s:
        return False
    # Must contain at least one letter
    if not re.search(r"[A-Za-z]", s):
        return False
    # Should not be mostly numeric
    if _is_numeric_cell(s):
        return False
    return True


def _normalize_header_token(token: str) -> str:
    return re.sub(r"\s+", " ", token.strip().lower())


def _header_semantics_ok(h0: str, h1: str, h2: str) -> Tuple[bool, str]:
    """
    Validate that headers correspond to event name, casualties, and difference semantics.
    """
    events_keywords = [
        "event", "event name", "accident", "disaster", "incident", "industrial accident",
        "industrial incident", "case", "scenario"
    ]
    casualties_keywords = [
        "casualties", "deaths", "fatalities", "injuries", "killed", "death toll", "injury count",
        "victims"
    ]
    difference_keywords = [
        "difference", "delta", "gap", "change", "diff", "variance", "vs", "comparison",
        "difference vs", "difference from", "difference to", "delta vs"
    ]

    h0n, h1n, h2n = _normalize_header_token(
        h0), _normalize_header_token(h1), _normalize_header_token(h2)

    def contains_any(token: str, kws: List[str]) -> bool:
        return any(kw in token for kw in kws)

    ok0 = contains_any(h0n, events_keywords)
    ok1 = contains_any(h1n, casualties_keywords)
    ok2 = contains_any(h2n, difference_keywords)
    if ok0 and ok1 and ok2:
        return True, ""
    missing = []
    if not ok0:
        missing.append(
            "first header should indicate event names (e.g., 'Event', 'Accident', 'Incident')")
    if not ok1:
        missing.append(
            "second header should indicate casualty numbers (e.g., 'Casualties', 'Deaths', 'Fatalities')")
    if not ok2:
        missing.append(
            "third header should indicate a difference column (e.g., 'Difference', 'Delta')")
    return False, "; ".join(missing)


# ---------------------------
# Markdown table parsing
# ---------------------------

def _parse_md_line(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_md_separator_line_for_cols(line: str, n_cols: int) -> bool:
    """
    Validate markdown header separator line for n_cols columns, like:
    | --- | --- | --- |
    or with colons for alignment: | :--- | ---: | :---: |
    """
    cols = _parse_md_line(line)
    if len(cols) != n_cols:
        return False
    for c in cols:
        if not re.fullmatch(r":?-{3,}:?", c.replace(" ", "")):
            return False
    return True


def _detect_markdown_table(response: str) -> Optional[Tuple[List[str], List[List[str]], Tuple[int, int]]]:
    """
    Detect and parse a Markdown table. Returns (headers, rows, (start_index, end_index)) in response,
    or None if no markdown table found.
    """
    lines = response.splitlines()
    # We'll scan for a header line followed by a separator line
    for i in range(len(lines) - 1):
        header_line = lines[i]
        if "|" not in header_line:
            continue
        header_cols = _parse_md_line(header_line)
        # Need at least 3 columns
        if len(header_cols) < 3:
            continue
        sep_idx = i + 1
        # Skip blank lines until we find potential separator
        while sep_idx < len(lines) and not lines[sep_idx].strip():
            sep_idx += 1
        if sep_idx >= len(lines):
            break
        sep_line = lines[sep_idx]
        if not _is_md_separator_line_for_cols(sep_line, len(header_cols)):
            continue

        # Collect data rows until a non-table line
        rows: List[List[str]] = []
        j = sep_idx + 1
        while j < len(lines):
            line = lines[j]
            if "|" not in line:
                break
            row_cols = _parse_md_line(line)
            # Require exact same number of columns as header
            if len(row_cols) != len(header_cols):
                break
            rows.append(row_cols)
            j += 1

        if rows:
            # Compute start/end indices in the raw response string
            # Reconstruct block content and find positions
            block = "\n".join(lines[i:j])
            start_pos = response.find(block)
            if start_pos == -1:
                # Fallback: approximate bounds
                start_pos = 0
            end_pos = start_pos + len(block)
            # Return only the first 3 columns even if header has more
            headers = header_cols
            return headers, rows, (start_pos, end_pos)
    return None


# ---------------------------
# HTML table parsing
# ---------------------------

def _detect_html_table(response: str) -> Optional[Tuple[List[str], List[List[str]], Tuple[int, int]]]:
    m = re.search(r"(?is)<table.*?>.*?</table>", response)
    if not m:
        return None
    table_html = m.group(0)
    # Extract rows
    rows_html = re.findall(r"(?is)<tr.*?>(.*?)</tr>", table_html)
    if not rows_html:
        return None

    # Header: first row's th or td cells
    header_cells = re.findall(r"(?is)<th.*?>(.*?)</th>", rows_html[0])
    if not header_cells:
        header_cells = re.findall(r"(?is)<td.*?>(.*?)</td>", rows_html[0])
    headers = [_strip_html_tags(c) for c in header_cells]
    if len(headers) < 3:
        return None

    # Data rows: subsequent rows -> td cells
    data_rows: List[List[str]] = []
    for r in rows_html[1:]:
        tds = re.findall(r"(?is)<td.*?>(.*?)</td>", r)
        if not tds:
            # Some HTML tables have th in body; fallback
            tds = re.findall(r"(?is)<t[hd].*?>(.*?)</t[hd]>", r)
        row = [_strip_html_tags(c) for c in tds]
        if len(row) != len(headers):
            # require consistent columns
            return None
        data_rows.append(row)

    if not data_rows:
        return None

    start_pos = m.start()
    end_pos = m.end()
    return headers, data_rows, (start_pos, end_pos)


# ---------------------------
# CSV/TSV table parsing
# ---------------------------

def _detect_delimited_table(response: str) -> Optional[Tuple[List[str], List[List[str]], Tuple[int, int], str]]:
    """
    Detect CSV (comma) or TSV (tab) tables with consistent column counts.
    Returns (headers, rows, (start, end), delim) or None.
    """
    lines = [ln for ln in response.splitlines() if ln.strip()]
    if not lines:
        return None

    # Attempt comma or tab delimiters
    for delim in [",", "\t"]:
        # Find first candidate header line
        for i in range(len(lines)):
            if delim in lines[i]:
                headers = [c.strip() for c in lines[i].split(delim)]
                if len(headers) < 3:
                    continue
                rows: List[List[str]] = []
                j = i + 1
                while j < len(lines) and delim in lines[j]:
                    row = [c.strip() for c in lines[j].split(delim)]
                    if len(row) != len(headers):
                        break
                    rows.append(row)
                    j += 1
                if rows:
                    # Compute raw indices
                    block = "\n".join(lines[i:j])
                    start_pos = response.find(block)
                    if start_pos == -1:
                        start_pos = 0
                    end_pos = start_pos + len(block)
                    return headers, rows, (start_pos, end_pos), delim
    return None


# ---------------------------
# Core validator for format
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response presents the final answer in a tabular format with exactly three columns:
    - Column 1: Event names (textual)
    - Column 2: Casualty numbers (numeric)
    - Column 3: Explicit difference (numeric)
    Returns (is_valid, message).
    The message is an English, detailed, actionable guidance for fixing any issues.
    """
    resp_trimmed = response.strip()
    if not resp_trimmed:
        return False, (
            "The response is empty. You must present the final answer as a table with exactly three columns: "
            "Event | Casualties | Difference. Use a Markdown table (preferred) and include at least one data row."
        )

    # Try to detect a table in common formats (Markdown, HTML, CSV/TSV)
    md = _detect_markdown_table(resp_trimmed)
    html = None if md else _detect_html_table(resp_trimmed)
    csv_tsv = None if (md or html) else _detect_delimited_table(resp_trimmed)

    table_type = None
    headers: List[str] = []
    rows: List[List[str]] = []
    block_bounds: Optional[Tuple[int, int]] = None

    if md:
        headers, rows, block_bounds = md
        table_type = "markdown"
    elif html:
        headers, rows, block_bounds = html
        table_type = "html"
    elif csv_tsv:
        headers, rows, block_bounds, _ = csv_tsv
        table_type = "delimited"
    else:
        return False, (
            "No valid table was detected in the response. You must output the final answer strictly as a table. "
            "Please use a Markdown table with a header separator row, for example:\n"
            "Event | Casualties | Difference\n"
            "| --- | --- | --- |\n"
            "Example Event A | 1,234 | 200\n"
            "Ensure exactly three columns, numeric values in the second and third columns, and include at least one data row."
        )

    # Enforce exactly 3 columns consistently
    if len(headers) != 3:
        return False, (
            f"The table has {len(headers)} columns, but it must have exactly three: "
            "Column 1 = Event names, Column 2 = Casualties, Column 3 = Difference. "
            "Revise the header to exactly three columns."
        )

    # Check all rows have exactly 3 columns
    for idx, r in enumerate(rows, start=1):
        if len(r) != 3:
            return False, (
                f"Row {idx} has {len(r)} columns but the table must have exactly three columns per row. "
                "Adjust the table so each row has exactly three cells: Event | Casualties | Difference."
            )

    # Require at least one data row
    if len(rows) < 1:
        return False, "The table contains no data rows. Include at least one row with Event, Casualties, and Difference values."

    # Validate header semantics
    ok_sem, why = _header_semantics_ok(headers[0], headers[1], headers[2])
    if not ok_sem:
        return False, (
            "Header semantics are incorrect: " + why +
            ". Update the header to clearly indicate columns as 'Event', 'Casualties', and 'Difference'."
        )

    # Validate cell types: first textual event, second numeric, third numeric
    for idx, r in enumerate(rows, start=1):
        event_cell, casualties_cell, diff_cell = r[0], r[1], r[2]
        if not _is_textual_event_name(event_cell):
            return False, (
                f"Row {idx} column 1 (event name) must be textual and contain letters (e.g., 'Texas City Disaster'). "
                f"Found: '{event_cell}'. Replace it with a descriptive event name."
            )
        if not _is_numeric_cell(casualties_cell):
            return False, (
                f"Row {idx} column 2 (casualties) must be numeric (e.g., '2,300' or '2300'). "
                f"Found: '{casualties_cell}'. Use digits only, optionally with thousand separators."
            )
        if not _is_numeric_cell(diff_cell):
            return False, (
                f"Row {idx} column 3 (difference) must be numeric (e.g., '150' or '-150'). "
                f"Found: '{diff_cell}'. Compute and provide the explicit difference as a number."
            )

    # Check for extraneous non-table text (final answer should be presented as a table, without preamble)
    if block_bounds:
        start, end = block_bounds
        pre = resp_trimmed[:start].strip()
        post = resp_trimmed[end:].strip()
        # Allow empty strings only
        if pre or post:
            # If there is just minimal markers like [FINAL ANSWER], still request removal
            return False, (
                "The final answer must be presented directly as the table without any extra text before or after. "
                "Remove any explanations, labels (e.g., '[FINAL ANSWER]'), or commentary and output only the table."
            )

    # If all checks pass
    return True, (
        "The response correctly presents a three-column table with proper headers and numeric values. "
        "Ensure the 'Difference' values are the explicitly computed numeric differences between the relevant casualty counts."
    )

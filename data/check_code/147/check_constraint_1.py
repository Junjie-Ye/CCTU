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

import re
import csv
from datetime import datetime
from typing import Tuple, List, Optional


# --------------------------
# Helper utilities
# --------------------------

def _is_md_separator(line: str) -> bool:
    """Detects a Markdown table separator row like |---|---|---| or ---|:---:|---"""
    s = line.strip()
    return bool(s) and all(ch in "-|: " for ch in s) and "-" in s


def _detect_delimiter(header_line: str) -> str:
    """Heuristically detect table delimiter among Markdown pipes, CSV commas, or TSV tabs."""
    if "|" in header_line:
        return "|"
    if "," in header_line:
        return ","
    if "\t" in header_line:
        return "\t"
    return ""


def _split_columns(line: str, delimiter: str) -> List[str]:
    """
    Split a table row into columns, trimming whitespace.

    - For Markdown pipe tables: split by '|' and trim, remove leading/trailing empty caused by border pipes.
    - For CSV/TSV: use csv.reader to correctly handle quoted fields and embedded delimiters.
    """
    if delimiter == "|":
        parts = [p.strip() for p in line.strip().split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        return parts

    # CSV/TSV robust parsing (handles quotes and embedded commas/tabs)
    try:
        row = next(csv.reader([line], delimiter=delimiter,
                   quotechar='"', skipinitialspace=True))
        return [c.strip() for c in row]
    except Exception:
        # fallback (should be rare)
        return [p.strip() for p in line.strip().split(delimiter)]


def _is_valid_iso_date(s: str) -> bool:
    """Validate YYYY-MM-DD format and actual calendar date."""
    s = s.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")  # 只要出现数字就算（可带符号/小数）


def _has_any_number(cols: List[str]) -> bool:
    """Return True if any cell contains at least one numeric token."""
    return any(_NUMBER_RE.search(c or "") for c in cols)


def _find_table_block(
    lines: List[str],
    expected_headers: List[str],
) -> Tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
    """
    Find a contiguous table block inside a response.
    Returns (header_idx, data_start_idx, delimiter, error_hint).
    """
    best_hint = None

    for i, ln in enumerate(lines):
        if not ln.strip():
            continue

        delimiter = _detect_delimiter(ln)
        if not delimiter:
            continue

        header_cols = _split_columns(ln, delimiter)
        if header_cols != expected_headers:
            continue

        # Found matching header; determine data start
        j = i + 1
        if delimiter == "|" and j < len(lines) and _is_md_separator(lines[j]):
            j += 1

        if j >= len(lines):
            best_hint = "Found header, but no data rows follow it."
            continue

        return i, j, delimiter, None

    if best_hint is None:
        best_hint = (
            "No matching table header found. You must include a table with headers exactly: "
            "Event | Date (YYYY-MM-DD) | Gap (Days). The table can appear in the middle of the response."
        )
    return None, None, None, best_hint


# --------------------------
# Validator
# --------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response CONTAINS a table with exact headers:
      'Event', 'Date (YYYY-MM-DD)', 'Gap (Days)'.

    Allow arbitrary text before/after the table. The validator will locate the first
    matching table block and validate:
    - Table must have >= 2 data rows total.
    - The last data row is treated as the GAP row.
      GAP row rule: among its 3 columns, at least one contains a number (any numeric token).
    - All preceding rows are treated as EVENT rows:
      EVENT row rules:
        * Event cell non-empty
        * Date cell is valid ISO date YYYY-MM-DD
    Supports Markdown pipe tables, CSV, or TSV.
    """
    text = (response or "")
    if not text.strip():
        return False, (
            "Response is empty. Provide some text plus a tabular answer (Markdown pipe table, CSV, or TSV) "
            "with headers: Event | Date (YYYY-MM-DD) | Gap (Days). Include at least one event row and a final gap row."
        )

    raw_lines = text.splitlines()
    expected_headers = ["Event", "Date (YYYY-MM-DD)", "Gap (Days)"]

    header_idx, data_start_idx, delimiter, hint = _find_table_block(
        raw_lines, expected_headers)
    if header_idx is None or data_start_idx is None or delimiter is None:
        return False, hint or "No valid table found."

    # Collect contiguous data rows until a boundary:
    # - blank line, OR
    # - cannot parse into exactly 3 columns
    rows: List[List[str]] = []
    for k in range(data_start_idx, len(raw_lines)):
        line = raw_lines[k]
        if not line.strip():
            break

        # For Markdown pipe tables, non-'|' lines end the block
        if delimiter == "|" and "|" not in line:
            break

        cols = _split_columns(line, delimiter)
        if len(cols) != 3:
            break

        rows.append(cols)

    # >= 2 data rows (>=1 event + 1 gap)
    if len(rows) < 2:
        return False, (
            "Insufficient data rows in the detected table. You must include at least one event row and one final gap row "
            "(>= 2 data rows) directly under the required header."
        )

    # Split into event rows and gap row
    event_rows = rows[:-1]
    gap_row = rows[-1]

    # Validate event rows (can be 1 or more)
    for idx, (event, date_str, _gap_cell) in enumerate(event_rows, start=1):
        if not event.strip():
            return False, f"Empty Event value in event row {idx}. Provide a clear event name or description."
        if not _is_valid_iso_date(date_str):
            return False, (
                f"Invalid date in event row {idx}: '{date_str}'. Dates must be valid ISO format YYYY-MM-DD "
                "(e.g., 1969-07-20)."
            )

    # Validate gap row: at least one number in any of the 3 columns
    if not _has_any_number(gap_row):
        return False, (
            "The final (gap) row must contain at least one numeric value in one of its three columns. "
            f"Found gap row: {gap_row!r}"
        )

    return True, (
        "Format is valid: found the required table header, >=2 data rows, event rows with valid ISO dates, "
        "and a final gap row containing at least one number."
    )

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
from typing import List, Tuple, Optional

NUMBER_RE = re.compile(r'[-+]?\d[\d,]*(\.\d+)?')

SPECIAL_NUMERIC_RE = re.compile(r'\b(?:nan|n/?a|na|ten)\b', re.IGNORECASE)


def _normalize_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _split_by_delim(line: str, delim: str = "||") -> List[str]:
    """
    Split by '||' and SUPPORT leading/trailing empty cells like:
      '||A||B||' -> ['A', 'B']
    """
    cols = [col.strip() for col in line.split(delim)]
    # strip leading/trailing empty cols caused by starting/ending delimiters
    while cols and cols[0] == "":
        cols.pop(0)
    while cols and cols[-1] == "":
        cols.pop()
    return cols


def _looks_like_header(cols: List[str]) -> bool:
    """
    Header heuristic: if any cell mentions 'description/desc' AND any cell mentions 'numeric/value/...'
    (works even when column count != 2)
    """
    low = [c.lower() for c in cols]
    has_desc = any(("description" in c or "desc" in c) for c in low)
    has_numeric = any(
        ("numeric" in c or "value" in c or "number" in c or "amount" in c) for c in low)
    return has_desc and has_numeric


def _extract_table_rows_with_delim(response: str, delim: str = "||") -> List[List[str]]:
    rows: List[List[str]] = []
    for ln in _normalize_lines(response):
        if delim in ln:
            cols = _split_by_delim(ln, delim=delim)
            # keep if at least one non-empty cell remains
            if any(c for c in cols):
                rows.append(cols)
    return rows


def _separate_header_and_data(rows: List[List[str]]) -> Tuple[List[List[str]], List[List[str]]]:
    headers, data = [], []
    for r in rows:
        if _looks_like_header(r):
            headers.append(r)
        else:
            data.append(r)
    return headers, data


def _numeric_in_text(text: str) -> bool:
    s = (text or "").strip()
    return bool(NUMBER_RE.search(s) or SPECIAL_NUMERIC_RE.search(s))


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Relaxed rules:
    - Accept '||A||B||' style (leading/trailing empty columns stripped).
    - Column count per row is flexible (>=1).
    - A "valid data row" is any non-header row that contains >=1 numeric-like cell in any column.
    - Require at least TWO valid data rows (for a and b), but allow extra rows.
    """
    rows = _extract_table_rows_with_delim(response, delim="||")
    if not rows:
        return (
            False,
            "No table lines using '||' were found. Add a table using '||' as column separator."
        )

    _, data_rows = _separate_header_and_data(rows)

    valid_data_rows = data_rows

    if len(valid_data_rows) < 2:
        return (
            False,
            f"Need at least two data rows (for the two values). Each data row may have ANY number of columns, "
            f"but must contain at least one numeric-looking cell. Found {len(valid_data_rows)} valid data rows."
        )

    return (
        True,
        f"Format OK: found {len(valid_data_rows)} numeric-containing data row(s) using '||' (>=2 required)."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    New rules:
    - Must use '||' somewhere in the table.
    - DO NOT enforce 'exactly one || per row' anymore.
    - Still forbid mixing single '|' with '||' in the same row.
    """
    lines = _normalize_lines(response)
    table_lines = [ln for ln in lines if "||" in ln]

    if not table_lines:
        used_single_pipe = any(('|' in ln and '||' not in ln) for ln in lines)
        if used_single_pipe:
            return (
                False,
                "Detected single '|' without '||'. Use '||' as the column separator."
            )
        return (
            False,
            "No '||' column separators found. Use '||' between columns in each table row."
        )

    problems = []
    for ln in table_lines:
        # Disallow mixing single '|' besides the '||' delimiters
        if '|' in ln.replace('||', ''):
            problems.append(
                f"Do not mix single '|' with '||' in the same row: '{ln}'")

        # Also ensure splitting (after trimming empty edges) still leaves something
        cols = _split_by_delim(ln, delim="||")
        if not cols:
            problems.append(
                f"Row becomes empty after trimming edge empty cells: '{ln}'")

    if problems:
        return (
            False,
            "Issues with '||' table rows: " + " | ".join(problems)
        )

    return (
        True,
        "Identifiers constraint satisfied: '||' is used as the delimiter without mixing single '|'."
    )

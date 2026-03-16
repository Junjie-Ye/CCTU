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
 The final answer must contain a table with at least three columns: the name of the feature, its depth, and the difference from the average depth of the Pacific Ocean. The table must include a header row and align the data vertically for clarity. The entire response must be between 200 and 300 characters in length to ensure clarity and conciseness while including the required tabular format. The final response must end with a period to ensure proper sentence closure. If the agent chooses to use the `factual_data_retriever` or `ocean_depth_analyzer` tools, their total invocation count must not exceed two per tool.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The final answer must contain a table with at least three columns: the name of the feature, its depth, and the difference from the average depth of the Pacific Ocean. The table must include a header row and align the data vertically for clarity.')
- idx 2: ('Response', 'Punctuation', '(Response, Punctuation, The final response must end with a period to ensure proper sentence closure.)')
"""

import re
from typing import Tuple, List, Optional

# Helper functions


def _non_empty_lines(s: str) -> List[str]:
    return [ln for ln in s.splitlines() if ln.strip()]


def _detect_delimiter(line: str) -> Optional[str]:
    if '|' in line and line.count('|') >= 2:
        return '|'
    if '\t' in line and line.count('\t') >= 2:
        return '\t'
    return None


def _split_cells(line: str, delim: str) -> List[str]:
    if delim == '|':
        line = line.strip()
        # Allow Markdown-style leading/trailing pipes
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        return [c.strip() for c in line.split('|')]
    else:  # '\t'
        return [c.strip() for c in line.split('\t')]


def _is_md_separator(line: str) -> bool:
    # Markdown header separator like: |---|:---:|---|
    return bool(re.fullmatch(r"\s*\|?\s*[:\-|\s]+\s*\|?\s*", line))


def _find_table(lines: List[str]):
    """
    Return (header_cells, data_rows_cells, delimiter) or (None, None, None) if not found.
    """
    for i, line in enumerate(lines):
        delim = _detect_delimiter(line)
        if not delim:
            continue
        header_cells = _split_cells(line, delim)
        if len([c for c in header_cells if c]) < 3:
            continue
        # Optional markdown header separator on next line
        j = i + 1
        if j < len(lines) and _is_md_separator(lines[j]):
            j += 1
        # Collect data rows with same column count
        data_rows = []
        while j < len(lines):
            dline = lines[j]
            if delim not in dline:
                break
            row_cells = _split_cells(dline, delim)
            if len(row_cells) != len(header_cells):
                break
            data_rows.append(row_cells)
            j += 1
        if data_rows:
            return header_cells, data_rows, delim
    return None, None, None


def _header_checks(header_cells: List[str]) -> Tuple[bool, str]:
    """
    Verify that header contains:
    - a feature/name column
    - a depth column
    - a difference-vs-Pacific-average column
    """
    hdr = [c.lower() for c in header_cells]

    has_feature = any(re.search(r"\b(name|feature)\b", c) for c in hdr)
    has_depth = any(re.search(r"\bdepth\b", c) for c in hdr)

    # "difference from the average depth of the Pacific Ocean"
    def is_diff_vs_pacific(c: str) -> bool:
        return "diff" in c.lower()

    has_diff_col = any(is_diff_vs_pacific(c) for c in hdr)

    if not has_feature:
        return False, "Header must include a feature/name column (e.g., 'Feature' or 'Name')."
    if not has_depth:
        return False, "Header must include a depth column labeled with 'Depth'."
    if not has_diff_col:
        return False, "Header must include a column describing the difference vs the Pacific average (e.g., 'Difference vs Pacific Avg')."

    return True, "OK"


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates:
    - Response length is between 200 and 300 characters (inclusive).
    - Contains a table with:
        * A header row.
        * At least 3 columns: feature/name, depth, difference vs Pacific average.
        * Consistent delimiter ('|' or '\\t').
        * All data rows have the same number of columns as header (vertical alignment).
    """
    # Length check

    lines = _non_empty_lines(response)
    if not lines:
        return False, "Response is empty; include a compact table with a header and data rows."

    header, data_rows, delim = _find_table(lines)
    if header is None:
        return (
            False,
            "No valid table detected. Use a compact pipe '|' or tab '\\t' table with a header and at least one data row. Example: 'Feature | Depth | Difference vs Pacific Avg\\nA | 100m | +50m'."
        )

    # Column count
    if len(header) < 3:
        return (
            False,
            f"Table must have at least 3 columns; detected {len(header)}. Include 'Feature/Name', 'Depth', and 'Difference vs Pacific Avg'."
        )

    # Consistent column counts across rows
    header_cols = len(header)
    inconsistent_rows = [idx for idx, row in enumerate(
        data_rows, start=1) if len(row) != header_cols]
    if inconsistent_rows:
        return (
            False,
            "All table rows must have the same number of columns for vertical alignment. Fix column counts across all rows so they match the header."
        )

    # Header semantics
    ok, msg = _header_checks(header)
    if not ok:
        return False, msg

    # Delimiter requirement for vertical alignment clarity
    if delim not in ('|', '\t'):
        return (
            False,
            "Use '|' or '\\t' as the column delimiter to ensure vertical alignment."
        )

    return True, "Format is valid: table detected with proper header, column count, and vertical alignment."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the final non-whitespace character is a period '.'.
    """
    m = re.search(r"\S\s*$", response)
    # Find last non-whitespace character
    last_non_ws = None
    for ch in reversed(response):
        if not ch.isspace():
            last_non_ws = ch
            break

    if last_non_ws != '.':
        return (
            False,
            "The final non-whitespace character must be a period '.'. Add a period at the very end of the response."
        )

    return True, "Punctuation is valid: response ends with a period."

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
 If the agent executes an interaction turn, it must include the simultaneous invocation of at least two unique tool types, you must complete the task in at most 10 interaction turns, you can make at most 10 tool calls in total across all interaction turns, you can call the 'historical_figure_monument_locator', 'landmark_locator', 'geographical_feature_identifier', 'enhanced_nearby_waterfall_locator', 'population_data_retriever', and 'landmark_info_retriever' tools at most once each, your final answer must end with either 'Answer: (a) the population is larger' or 'Answer: (b) the height is larger', and your final response must contain a table with clear headers and organized data for comparison.

response_constraints_non_length:
- idx 4: ('Response', 'Identifiers', "(Main Category, Response, End identifier (The final response must end with 'Answer: (a) the population is larger' or 'Answer: (b) the height is larger')).")
- idx 5: ('Response', 'Format', "(Mandates that the agent's response must contain a table, using rows and columns to clearly present data. This includes proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information.)")
"""

import re
from typing import Tuple, List, Optional


# -----------------------------
# Helper utilities
# -----------------------------

def _last_nonempty_line(text: str) -> Optional[str]:
    """Return the last non-empty (non-whitespace) line, or None if none exists."""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _is_pipe_line(line: str) -> bool:
    """Heuristic: returns True if line looks like a Markdown table row with pipes."""
    return bool(re.match(r'^\s*\|.*\|\s*$', line))


def _is_md_separator(line: str) -> bool:
    return bool(re.match(r'^\s*\|\s*(?::?-{3,}:?\s*\|\s*)+\s*$', line))


def _split_md_cells(line: str) -> List[str]:
    """Split a Markdown table row into cells, trimming outer pipes and whitespace."""
    # Remove leading/trailing pipes
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    # Split on '|' and strip each cell
    cells = [c.strip() for c in line.split('|')]
    return cells


def _find_markdown_tables(text: str) -> List[dict]:
    """
    Parse potential Markdown tables in the text.
    Returns a list of dicts with keys:
      - header: List[str]
      - rows: List[List[str]]
      - start_idx, end_idx: line indices (inclusive for end_idx)
    Only includes tables that have header + separator + >=1 data row.
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines) - 1:
        if _is_pipe_line(lines[i]) and _is_md_separator(lines[i + 1]):
            header_cells = _split_md_cells(lines[i])
            sep_line = lines[i + 1]
            # Collect data rows
            j = i + 2
            data_rows = []
            while j < len(lines) and _is_pipe_line(lines[j]):
                data_rows.append(_split_md_cells(lines[j]))
                j += 1

            # Only accept if at least one data row
            if data_rows:
                tables.append({
                    'header': header_cells,
                    'rows': data_rows,
                    'start_idx': i,
                    'end_idx': j - 1
                })
            i = j
        else:
            i += 1
    return tables


def _validate_markdown_table_structure(table: dict) -> Tuple[bool, str]:
    """
    Validate a parsed Markdown table for:
    - Non-empty header cells
    - At least two columns
    - All rows have identical column counts matching header
    - Header separator already guaranteed by parser
    """
    header = table['header']
    rows = table['rows']

    if len(header) < 2:
        return False, "A valid Markdown table must have at least two columns."

    if any((not cell or cell.strip('-:') == '') for cell in header):
        return False, "Header cells must be non-empty descriptive labels (not just dashes/colons)."

    header_cols = len(header)
    for idx, row in enumerate(rows, start=1):
        if len(row) != header_cols:
            return False, f"Row {idx} has {len(row)} cells, but the header has {header_cols}. All rows must have identical column counts."

    return True, "Valid Markdown table with headers and consistent column counts."


def _is_ascii_border(line: str) -> bool:
    """
    Detect ASCII grid border lines like:
    +-----+-----+ or +=====+=====+
    """
    return bool(re.match(r'^\s*\+(?:[=\-]+)(?:\+(?:[=\-]+))*\+\s*$', line))


def _is_ascii_row(line: str) -> bool:
    """
    Detect ASCII grid row lines like:
    | data | more |
    """
    return bool(re.match(r'^\s*\|.*\|\s*$', line))


def _find_ascii_tables(text: str) -> List[dict]:
    """
    Parse potential ASCII grid tables. Returns list of dicts:
      - rows: List[str] (row lines with data)
      - borders: List[str] (border lines)
      - start_idx, end_idx: line indices
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        if _is_ascii_border(lines[i]):
            start = i
            i += 1
            row_lines = []
            border_lines = [lines[start]]
            # Expect alternating rows and borders
            while i < len(lines):
                if _is_ascii_row(lines[i]):
                    row_lines.append(lines[i])
                    i += 1
                else:
                    break
                if i < len(lines) and _is_ascii_border(lines[i]):
                    border_lines.append(lines[i])
                    i += 1
                else:
                    break
            if row_lines and len(border_lines) >= 2:
                tables.append({
                    'rows': row_lines,
                    'borders': border_lines,
                    'start_idx': start,
                    'end_idx': i - 1
                })
        else:
            i += 1
    return tables


def _validate_ascii_table_structure(table: dict) -> Tuple[bool, str]:
    """
    Validate ASCII grid tables for:
    - At least two columns (i.e., >= 3 '|' per row)
    - All row lines have the same '|' positions (consistent columns)
    - At least two row lines (header + one data row recommended)
    """
    rows = table['rows']
    if len(rows) < 2:
        return False, "ASCII table should include at least a header row and one data row."

    # Determine '|' positions for alignment consistency
    def bar_positions(s: str) -> List[int]:
        return [i for i, ch in enumerate(s) if ch == '|']

    ref_positions = bar_positions(rows[0])
    if len(ref_positions) < 3:
        return False, "ASCII table must have at least two columns (i.e., at least three '|' characters per row)."

    for idx, r in enumerate(rows, start=1):
        pos = bar_positions(r)
        if pos != ref_positions:
            return False, f"Row {idx} column separators are misaligned. All rows must align vertical bars '|' at the same indices."

    return True, "Valid ASCII table with consistent column alignment and at least two rows."


# -----------------------------
# Validators for constraints
# -----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates the 'format' response constraint:
    - The response must contain a table with rows and columns.
    - Proper use of headers (clear header labels).
    - Consistent column widths/alignment (i.e., consistent column counts/positions).
    Accepts either a Markdown table or an ASCII grid table.
    """
    # First, try to find and validate a Markdown table
    md_tables = _find_markdown_tables(response)
    for t in md_tables:
        ok, msg = _validate_markdown_table_structure(t)
        if ok:
            return True, "Format OK: A well-formed Markdown table with headers and consistent columns was detected."

    # If no valid Markdown table, try ASCII tables
    ascii_tables = _find_ascii_tables(response)
    for t in ascii_tables:
        ok, msg = _validate_ascii_table_structure(t)
        if ok:
            return True, "Format OK: A well-formed ASCII table with consistent columns was detected. Ensure the first row clearly serves as headers."

    # Construct detailed guidance if none passed
    issues = []
    if md_tables:
        # Some Markdown-like constructs were found but invalid
        for idx, t in enumerate(md_tables, start=1):
            ok, msg = _validate_markdown_table_structure(t)
            if not ok:
                issues.append(f"Markdown table {idx}: {msg}")
    if ascii_tables:
        for idx, t in enumerate(ascii_tables, start=1):
            ok, msg = _validate_ascii_table_structure(t)
            if not ok:
                issues.append(f"ASCII table {idx}: {msg}")

    guidance = (
        "No valid table detected. Your final response must include a clear table for comparison.\n"
        "- Prefer a Markdown table with a header row and a separator line, e.g.:\n"
        "  | City Population | Waterfall Height |\n"
        "  | ---: | ---: |\n"
        "  | 1,234,567 | 123 m |\n"
        "- Requirements:\n"
        "  1) Include a header row with descriptive, non-empty labels.\n"
        "  2) Provide at least two columns and one data row.\n"
        "  3) Ensure every row has the same number of cells as the header.\n"
        "  4) For ASCII tables, align '|' vertically and keep column widths consistent across all rows."
    )
    if issues:
        guidance += "\nDetected issues:\n- " + "\n- ".join(issues)

    return False, guidance


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'identifiers' response constraint:
    - The final response must end with either:
      'Answer: (a) the population is larger'
      or
      'Answer: (b) the height is larger'
    The match is case-sensitive and must be the last non-empty line.
    """
    allowed_endings = [
        "Answer: (a) the population is larger",
        "Answer: (b) the height is larger",
    ]

    last_line = _last_nonempty_line(response or "")
    if last_line is None:
        return False, (
            "The response is empty. It must end with exactly one of the following lines:\n"
            "- Answer: (a) the population is larger\n"
            "- Answer: (b) the height is larger"
        )

    if last_line in allowed_endings:
        return True, "Identifiers OK: The final non-empty line matches the required 'Answer: (...)' identifier."

    # Provide actionable feedback
    fixes = []
    for ending in allowed_endings:
        if last_line.startswith(ending):
            # Extra trailing characters present
            extra = last_line[len(ending):]
            fixes.append(
                f"Remove any extra characters after the required ending. Found trailing: {repr(extra)}"
            )

    # Check if one of the allowed endings appears elsewhere in the response but not on the last line
    found_elsewhere = []
    for ending in allowed_endings:
        pattern = re.escape(ending)
        # Find all occurrences
        if re.search(pattern, response):
            if last_line != ending:
                found_elsewhere.append(ending)

    guidance = (
        "The final non-empty line must be exactly one of the following (case-sensitive):\n"
        "- Answer: (a) the population is larger\n"
        "- Answer: (b) the height is larger\n"
        f"Your current last line is: {repr(last_line)}"
    )

    if fixes:
        guidance += "\nFix suggestion:\n- " + "\n- ".join(fixes)

    if found_elsewhere:
        guidance += (
            "\nNote: A required identifier was found elsewhere in the response but not at the very end. "
            "Move it to the final non-empty line without any trailing characters:"
            "\n- " + "\n- ".join(found_elsewhere)
        )

    guidance += "\nEnsure there is no text or punctuation after the required ending line (only optional trailing whitespace is allowed)."

    return False, guidance

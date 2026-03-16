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
 Your answer must include the identifier 'AGREEMENT:' immediately before stating the name of the agreement to clearly delimit the agreement's name in the response. The response must contain a tabular format using rows and columns to clearly present data, with proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information. Additionally, you must ensure that the total number of tool calls executed across all interaction turns does not exceed three, and the tool `historical_agreement_finder` can be used at most once. The response must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Main Category, Subcategory, "The agent\'s response must include the identifier \'AGREEMENT:\' immediately before stating the name of the agreement to clearly delimit the agreement\'s name in the response.")')
- idx 2: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period to ensure proper sentence closure.)')
- idx 3: ('Response', 'Format', 'Table (The response must contain a tabular format, using rows and columns to clearly present data. This includes proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information.)')
"""

import re
from typing import Tuple, List, Optional

# Helpers and shared constants

EXPECTED_HEADERS = ["Date", "Parties Involved",
                    "Key Provisions", "Status (Active/Inactive)"]


def _normalize(text: str) -> str:
    """Normalize line endings to '\n' and strip trailing spaces per line."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _line_starts_and_ends_with_pipe(line: str) -> bool:
    line = line.rstrip("\n")
    return line.strip().startswith("|") and line.strip().endswith("|")


def _raw_segments(line: str) -> Optional[List[str]]:
    """
    Return raw (untrimmed) cell segments between pipes.
    Requires the line to start and end with '|'.
    """
    if not _line_starts_and_ends_with_pipe(line):
        return None
    parts = line.strip().split("|")
    # strip() puts empty '' at both ends because of leading/trailing pipe
    # e.g. "| a | b |" -> ["", " a ", " b ", ""]
    if len(parts) < 3:
        return None
    return parts[1:-1]  # raw, includes spaces for width checks


def _trimmed_cells(line: str) -> Optional[List[str]]:
    segs = _raw_segments(line)
    if segs is None:
        return None
    return [s.strip() for s in segs]


def _is_separator_line(line: str, expected_cols: int) -> bool:
    """
    Validate a Markdown-like separator row:
    - starts/ends with '|'
    - has the expected number of column segments
    - each segment contains at least 3 '-' and may include optional leading/trailing ':'
    - only characters allowed inside a segment: '-', ':', and spaces
    """
    if not _line_starts_and_ends_with_pipe(line):
        return False
    segs = _raw_segments(line)
    if segs is None or len(segs) != expected_cols:
        return False
    for seg in segs:
        s = seg.strip()
        if not s:
            return False
        # Only '-', ':', and spaces allowed
        if not re.fullmatch(r"[:\- ]+", s):
            return False
        # Must contain at least 3 hyphens (ignoring colons/spaces)
        dashes = re.sub(r"[: ]", "", s)
        if len(dashes) < 3 or set(dashes) != {"-"}:
            return False
    return True


def _find_first_table_block(text: str) -> Optional[Tuple[int, str, str, List[str]]]:
    """
    Find the first Markdown-like table block and return:
    (start_index, header_line, separator_line, data_lines[])
    The block must be contiguous lines that start/end with '|'.
    """
    lines = _normalize(text).split("\n")
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if _line_starts_and_ends_with_pipe(line):
            header_cells = _trimmed_cells(line)
            if header_cells is None:
                i += 1
                continue
            # Expect at least 1 more line for separator
            if i + 1 >= n:
                i += 1
                continue
            sep_line = lines[i + 1]
            if not _line_starts_and_ends_with_pipe(sep_line):
                i += 1
                continue
            # Validate separator with same number of columns as header
            if not _is_separator_line(sep_line, len(header_cells)):
                i += 1
                continue
            # Collect data rows
            data_rows: List[str] = []
            j = i + 2
            while j < n and _line_starts_and_ends_with_pipe(lines[j]):
                # Ensure same column count as header
                row_cells = _trimmed_cells(lines[j])
                if row_cells is None or len(row_cells) != len(header_cells):
                    break
                data_rows.append(lines[j])
                j += 1
            if data_rows:
                return (i, lines[i], sep_line, data_rows)
        i += 1
    return None


def _check_aligned_columns(lines: List[str]) -> Tuple[bool, str]:
    """
    Check that all provided lines have:
    - same number of columns
    - consistent column widths via space padding (so '|' align vertically)
    This is enforced by requiring each column segment to have the same length across lines.
    """
    if not lines:
        return False, "No lines provided to alignment checker."
    seg_lists: List[List[str]] = []
    for idx, line in enumerate(lines):
        segs = _raw_segments(line)
        if segs is None:
            return False, f"Line {idx + 1} does not start and end with '|' or is malformed."
        seg_lists.append(segs)
    col_count = len(seg_lists[0])
    for segs in seg_lists:
        if len(segs) != col_count:
            return False, "Inconsistent number of columns across table lines; ensure every line has the same number of '|' separators and cells."
    # Compute max width per column across lines
    max_widths = [0] * col_count
    for segs in seg_lists:
        for c in range(col_count):
            max_widths[c] = max(max_widths[c], len(segs[c]))
    # Require each segment to be padded (right or both sides) to the same width
    failing_cols = set()
    failing_rows = []
    for r, segs in enumerate(seg_lists):
        for c in range(col_count):
            if len(segs[c]) != max_widths[c]:
                failing_cols.add(c + 1)
                failing_rows.append(r + 1)
    if failing_cols:
        cols_str = ", ".join(str(c) for c in sorted(failing_cols))
        return (
            False,
            f"Columns are not width-aligned. Pad cells with spaces so each column segment has the same width across lines. "
            f"Columns failing width check: {cols_str}. Ensure vertical '|' characters line up across header and all data rows."
        )
    return True, "Columns appear width-aligned across all table lines."

# Validators


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    The agent's response must include the identifier 'AGREEMENT:' immediately before the agreement's name,
    and it must begin the response.
    """
    text = _normalize(response)
    # Must start with AGREEMENT: (allow leading whitespace to be robust, but instruct to start at the very beginning)
    if not re.match(r"^\s*AGREEMENT:\s*\S", text):
        return (
            False,
            "The response must begin with 'AGREEMENT:' followed by the agreement name on the same line. "
            "Example: \"AGREEMENT: Ohrid Framework Agreement\". Do not include any text before this identifier."
        )
    # Ensure it is truly at the beginning (no preamble content)
    if not text.lstrip().startswith("AGREEMENT:"):
        return (
            False,
            "Place 'AGREEMENT:' at the very start of the response (no preceding characters or whitespace)."
        )
    # Ensure non-empty name after the identifier on the same line
    first_line = text.lstrip().split("\n", 1)[0]
    m = re.match(r"^AGREEMENT:\s*(\S.*)$", first_line)
    if not m or not m.group(1).strip():
        return (
            False,
            "Provide a non-empty agreement name immediately after 'AGREEMENT:' on the same line."
        )
    return True, "Identifier is present at the start and properly followed by a non-empty agreement name."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    The response must end with a period '.' to ensure proper sentence closure.
    """
    text = _normalize(response)
    if not text.strip().endswith("."):
        return (
            False,
            "End the entire response with a period '.' as the final character. "
            "If your last content is a table, add a new line containing just '.' after the table."
        )
    return True, "The response ends with a period."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    The response must contain a tabular format (Markdown-like table) with:
    - A header row with EXACT headers: Date | Parties Involved | Key Provisions | Status (Active/Inactive)
    - A separator row (pipes and dashes, optional colons for alignment)
    - At least one data row
    - Consistent column widths and alignment across lines (pipes '|' should align vertically)
    """
    text = _normalize(response)
    found = _find_first_table_block(text)
    if not found:
        return (
            False,
            "No valid Markdown-style table detected. Include a table block with lines that start and end with '|'. "
            "The table must include: a header row, a separator row of pipes/dashes, and at least one data row. "
            "Headers must be exactly: | Date | Parties Involved | Key Provisions | Status (Active/Inactive) |"
        )
    start_idx, header_line, sep_line, data_lines = found
    header_cells = _trimmed_cells(header_line)
    if header_cells is None:
        return (
            False,
            "Malformed header row. Ensure the header line starts and ends with '|' and contains 4 cells."
        )
    if header_cells != EXPECTED_HEADERS:
        return (
            False,
            "Incorrect table headers. Use exactly these headers in this order: "
            "'Date', 'Parties Involved', 'Key Provisions', 'Status (Active/Inactive)'. "
            "Example header: | Date | Parties Involved | Key Provisions | Status (Active/Inactive) |"
        )
    # Validate separator line again for clarity
    if not _is_separator_line(sep_line, len(header_cells)):
        return (
            False,
            "The line immediately below the header must be a separator row composed of pipes and at least three dashes "
            "per column (e.g., |------|------|------|------|). Optional colons may be added for alignment."
        )
    # Validate all data rows have proper structure
    for idx, row in enumerate(data_lines, start=1):
        cells = _trimmed_cells(row)
        if cells is None or len(cells) != len(header_cells):
            return (
                False,
                f"Data row {idx} is malformed. Ensure every table line starts and ends with '|' and has exactly 4 cells."
            )
        # Ensure cells are non-empty (they can be minimal but should not be blank)
        if any(c.strip() == "" for c in cells):
            return (
                False,
                f"Data row {idx} contains empty cells. Provide content for each column or use a placeholder like 'N/A'."
            )
    # Check column alignment/width consistency across header and data rows
    alignment_ok, alignment_msg = _check_aligned_columns(
        [header_line] + data_lines)
    if not alignment_ok:
        return (
            False,
            alignment_msg + " Pad with spaces within cells so that '|' separators are vertically aligned for all rows."
        )
    return True, "Valid table detected with required headers, separator, data rows, and aligned columns."

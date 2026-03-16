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
 The answer must be presented in a tabular format with two columns: "Company Name" and "Resulting Company", and one row for each company formed from the split of Centura Health and must be immediately followed by a brief concluding sentence. The response must end with a period. You must use the provided tools to obtain the information, and you must complete this task in at most 2 interaction turns, using at most one tool call in total.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The final answer must be presented in a tabular format with two columns: "Company Name" and "Resulting Company", and one row for each company formed from the split of Centura Health. The table must be immediately followed by a brief concluding sentence.')
- idx 2: ('Response', 'Punctuation', 'The response must end with a period.')
"""

import re
from typing import List, Tuple, Optional, Dict

# -------- Helper utilities --------


def _split_md_row(line: str) -> Optional[List[str]]:
    """
    Split a Markdown table row into cells.
    Returns None if the line does not look like a Markdown table row.
    """
    if '|' not in line:
        return None
    # Trim and split, then remove leading/trailing empty cells caused by edge pipes
    parts = [p.strip() for p in line.strip().split('|')]
    if parts and parts[0] == '':
        parts = parts[1:]
    if parts and parts[-1] == '':
        parts = parts[:-1]
    # If any content remains, we consider it a row
    if len(parts) == 0:
        return None
    return parts


def _is_md_separator(line: str, expected_cols: int) -> bool:
    """
    Check if a line is a valid Markdown table separator row for a given column count.
    E.g., | --- | :---: | ---: |
    """
    cells = _split_md_row(line)
    if not cells or len(cells) != expected_cols:
        return False
    for cell in cells:
        if not re.fullmatch(r':?-{3,}:?', cell):
            return False
    return True


def _parse_markdown_table(lines: List[str], start_idx: int) -> Optional[Dict]:
    """
    Attempt to parse a Markdown table starting at start_idx.
    Returns a dict with keys: type, header, rows, start, end; or None if not a table.
    """
    header_cells = _split_md_row(lines[start_idx])
    if not header_cells:
        return None

    # Need a separator line next
    if start_idx + 1 >= len(lines):
        return None
    if not _is_md_separator(lines[start_idx + 1], len(header_cells)):
        return None

    rows: List[List[str]] = []
    i = start_idx + 2
    while i < len(lines):
        cells = _split_md_row(lines[i])
        if not cells or len(cells) != len(header_cells) or _is_md_separator(lines[i], len(header_cells)):
            break
        rows.append(cells)
        i += 1

    return {
        'type': 'markdown',
        'header': header_cells,
        'rows': rows,
        'start': start_idx,
        'end': i - 1 if rows else start_idx + 1  # end at separator if no data rows
    }


def _parse_delimited_table(lines: List[str], start_idx: int, delimiter: str) -> Optional[Dict]:
    """
    Parse a strictly delimited (CSV or TSV) table. The header must be exactly 2 columns.
    The table ends at the first blank line or a line that cannot be split into exactly 2 cells.
    """
    header_line = lines[start_idx].strip()
    if not header_line:
        return None
    header_cells = [c.strip() for c in header_line.split(delimiter)]
    if len(header_cells) != 2:
        return None

    rows: List[List[str]] = []
    i = start_idx + 1
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            break
        cells = [c.strip() for c in line.split(delimiter)]
        if len(cells) != 2:
            break
        rows.append(cells)
        i += 1

    return {
        'type': f'delimited({repr(delimiter)})',
        'header': header_cells,
        'rows': rows,
        'start': start_idx,
        # header-only table is allowed here; will be validated later
        'end': i - 1 if rows else start_idx
    }


def _find_table(response: str) -> Optional[Dict]:
    """
    Find the first table in the response. Supports:
    - Markdown tables with pipes and a separator row.
    - CSV tables with comma delimiter.
    - TSV tables with tab delimiter.
    Returns a dict with parsed table data or None if not found.
    """
    lines = response.splitlines()

    # Try Markdown tables first
    for i in range(len(lines)):
        parsed = _parse_markdown_table(lines, i)
        if parsed:
            return parsed

    # Try CSV
    for i in range(len(lines)):
        parsed = _parse_delimited_table(lines, i, ',')
        if parsed:
            return parsed

    # Try TSV
    for i in range(len(lines)):
        parsed = _parse_delimited_table(lines, i, '\t')
        if parsed:
            return parsed

    return None


def _has_nonempty_line(lines: List[str]) -> bool:
    return any(line.strip() for line in lines)


def _only_whitespace(s: str) -> bool:
    return len(s.strip()) == 0


def _line_looks_like_table(line: str) -> bool:
    # Heuristic: Markdown table or delimited form indicators
    if '|' in line:
        return True
    if ',' in line and len([c for c in line.split(',')]) >= 2:
        return True
    if '\t' in line and len([c for c in line.split('\t')]) >= 2:
        return True
    return False


# -------- Validators --------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The final answer is presented as a two-column table with headers "Company Name" and "Resulting Company".
    - The table appears first (no preface content).
    - There is at least one data row (strongly recommended: two rows for the two resulting companies).
    - The table is immediately followed by exactly one brief concluding sentence (no extra content).
    """
    if _only_whitespace(response):
        return False, "The response is empty. Provide a two-column table followed by a brief concluding sentence."

    parsed = _find_table(response)
    if not parsed:
        return False, "No table detected. Start the response with a two-column table. A Markdown table is recommended."

    lines = response.splitlines()
    start = parsed['start']
    end = parsed['end']
    header = parsed['header']
    rows = parsed['rows']

    # Ensure no preface content before the table
    preface_lines = lines[:start]
    if _has_nonempty_line(preface_lines):
        return False, "Remove any introductory text. The table must appear at the very beginning of the response."

    # Header validation: exactly "Company Name" and "Resulting Company"
    expected_headers = ["Company Name", "Resulting Company"]
    if len(header) != 2:
        return False, 'The table must have exactly two columns with headers "Company Name" and "Resulting Company".'
    # Normalize header cells by stripping surrounding quotes if present
    norm_header = [re.sub(r'^[\'"]|[\'"]$', '', h.strip()) for h in header]
    if [h.strip() for h in norm_header] != expected_headers:
        return False, 'The table headers must be exactly "Company Name" and "Resulting Company" in that order.'

    # Data rows validation
    if len(rows) == 0:
        return False, "Add at least one data row to the table; include a separate row for each resulting company from the split."
    if any(len(r) != 2 for r in rows):
        return False, "Each data row must have exactly two cells aligning with the two headers."

    # Strong recommendation: at least two rows (since a split typically yields two resulting companies)
    if len(rows) < 2:
        return False, "Provide a separate row for each resulting company. Include at least two rows."

    # Validate the concluding sentence immediately follows the table
    tail_lines = lines[end + 1:] if end + 1 < len(lines) else []
    # Allow at most one blank line between the table and the sentence
    idx = 0
    while idx < len(tail_lines) and tail_lines[idx].strip() == "":
        idx += 1
    # Now, the next non-empty line should be the concluding sentence
    if idx >= len(tail_lines):
        return False, "Add a brief concluding sentence immediately after the table."
    concluding = tail_lines[idx].strip()

    # Ensure only a single concluding sentence line remains
    remaining_after_conclusion = tail_lines[idx + 1:]
    if _has_nonempty_line(remaining_after_conclusion):
        return False, "Only one brief concluding sentence is allowed after the table. Remove any additional content."

    # Concluding sentence should not look like a table line
    if _line_looks_like_table(concluding):
        return False, "The line after the table must be a brief concluding sentence, not another table or list."

    # Reasonable brevity check (not more than 200 chars)
    if len(concluding) > 200:
        return False, "Shorten the concluding sentence to be brief (ideally under 200 characters)."

    return True, "Format is valid: two-column table with correct headers, followed by a single brief concluding sentence."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    """
    if _only_whitespace(response):
        return False, "The response is empty. Ensure the final character of the response is a period."
    trimmed = response.rstrip()
    if not trimmed.endswith('.'):
        return False, "The response must end with a period. Add a period to the very end of the concluding sentence."
    return True, "Punctuation is valid: the response ends with a period."

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
 You must use the provided tools to derive your answer, and you must not exceed 10 interaction turns in total. If the agent intends to retrieve both the seating capacity and ocean species data, the venue_information_retriever and species_record_locator tools must be invoked in the same action step. The city_feature_identifier tool must be called first in the process. The species_record_locator tool must be called at most 2 times. Your final answer must be presented in a tabular format, clearly listing each component of the calculation (theater seating capacity, number of ocean species, and their sum) in separate rows and columns to enhance clarity and accessibility.

response_constraints_non_length:
- idx 2: ('Response', 'Format', 'Final answer must be presented in a tabular format, clearly listing each component of the calculation (theater seating capacity, number of ocean species, and their sum) in separate rows and columns to enhance clarity and accessibility.')
"""

import re
from typing import List, Tuple, Optional

# -------------------------------
# Helpers: common parsing utilities
# -------------------------------


def _normalize_text(s: str) -> str:
    """Lowercase, collapse spaces, and strip surrounding whitespace for robust comparisons."""
    return re.sub(r'\s+', ' ', s or '').strip().lower()


def _looks_numeric_or_unknown(value: str) -> bool:
    """
    Accept numbers (int/float, optionally wrapped with []), or explicit unknown markers.
    Examples accepted: 1200, 1,200, 1200.0, [1200], unknown, unavailable, not found, n/a.
    """
    v = (value or '').strip()
    # Allow commas in numbers; allow square brackets around.
    numeric_pat = r'^\[?\s*-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*\]?$|^\[?\s*-?\d+(?:\.\d+)?\s*\]?$'
    if re.match(numeric_pat, v):
        return True
    v_norm = _normalize_text(v)
    return any(tok in v_norm for tok in ['unknown', 'unavailable', 'not found', 'n/a', 'na'])

# -------------------------------
# Markdown table parsing
# -------------------------------


def _is_md_alignment_row(line: str) -> bool:
    """
    Detects Markdown alignment rows like:
    | --- | :---: | ---: |
    or without leading/trailing pipes.
    """
    # Remove spaces around pipes for simpler check
    s = line.strip()
    # Quick reject if no '-' in line
    if '-' not in s:
        return False
    # Pattern: one or more segments separated by pipes, each segment is :?-{3,}:?
    cell_pat = r'\s*:?-{3,}:?\s*'
    patt = r'^\|?' + cell_pat + r'(?:\|' + cell_pat + r')+\|?$'
    return re.match(patt, s) is not None


def _is_md_table_line(line: str) -> bool:
    """
    A very permissive check for a Markdown table line:
    - Contains at least one pipe and has non-empty content separated by a pipe.
    """
    if '|' not in line:
        return False
    # It should have at least two non-empty tokens overall
    parts = [c.strip() for c in line.strip().split('|')]
    non_empty = [p for p in parts if p]
    return len(non_empty) >= 2


def _split_md_row(line: str) -> List[str]:
    """Split a Markdown table row into cells, trimming whitespace and removing leading/trailing empty cells."""
    parts = [c.strip() for c in line.split('|')]
    # Remove leading/trailing empties due to leading/trailing pipes
    if parts and parts[0] == '':
        parts = parts[1:]
    if parts and parts[-1] == '':
        parts = parts[:-1]
    return parts


def _extract_markdown_tables(text: str) -> List[List[List[str]]]:
    """
    Extract Markdown-style tables from text.
    Returns a list of tables; each table is a list of rows; each row is a list of cell strings.
    """
    tables: List[List[List[str]]] = []
    lines = text.splitlines()
    in_code = False
    current_block: List[str] = []

    for raw in lines:
        line = raw.rstrip('\n')
        # Toggle code block state
        if re.match(r'^\s*```', line):
            in_code = not in_code
            # Close any ongoing table if entering or exiting code block
            if current_block:
                tables.extend(_finalize_md_block(current_block))
                current_block = []
            continue

        if in_code:
            # Ignore code-fenced content for table detection
            if current_block:
                tables.extend(_finalize_md_block(current_block))
                current_block = []
            continue

        if _is_md_table_line(line):
            current_block.append(line)
        else:
            if current_block:
                tables.extend(_finalize_md_block(current_block))
                current_block = []

    if current_block:
        tables.extend(_finalize_md_block(current_block))

    return tables


def _finalize_md_block(block_lines: List[str]) -> List[List[List[str]]]:
    """
    Given a contiguous block of 'table-like' lines, segment it into actual tables by blank lines or
    runs that fail minimal structural checks. Then convert to cell matrices.
    """
    # Split on blank lines within the block (defensive)
    segmented: List[List[str]] = []
    buf: List[str] = []
    for ln in block_lines:
        if ln.strip() == '':
            if buf:
                segmented.append(buf)
                buf = []
        else:
            buf.append(ln)
    if buf:
        segmented.append(buf)

    tables: List[List[List[str]]] = []
    for seg in segmented:
        # Remove Markdown alignment rows
        filtered = [ln for ln in seg if not _is_md_alignment_row(ln)]
        # After filtering, we still need at least 2 lines to form a table (header + 1 row) or 3 data rows total
        if len(filtered) < 2:
            continue
        # Convert to cells
        cell_rows = [_split_md_row(ln) for ln in filtered]
        # Ensure each row has at least 2 columns
        cell_rows = [r for r in cell_rows if len(
            [c for c in r if c != '']) >= 2]
        if len(cell_rows) >= 2:
            tables.append(cell_rows)
    return tables

# -------------------------------
# HTML table parsing (fallback)
# -------------------------------


def _strip_html_tags(s: str) -> str:
    """Very naive HTML tag stripper for small fragments like <th>Header</th>."""
    # Replace <br> with space to avoid concatenation
    s = re.sub(r'<\s*br\s*/?\s*>', ' ', s, flags=re.IGNORECASE)
    return re.sub(r'<[^>]+>', '', s).strip()


def _extract_html_tables(text: str) -> List[List[List[str]]]:
    """
    Extract HTML tables: <table>...</table>. Each table is a list of rows; each row is a list of cell strings.
    """
    tables: List[List[List[str]]] = []
    for m in re.finditer(r'<table\b[^>]*>(.*?)</table>', text, flags=re.IGNORECASE | re.DOTALL):
        table_html = m.group(1)
        rows: List[List[str]] = []
        for r in re.finditer(r'<tr\b[^>]*>(.*?)</tr>', table_html, flags=re.IGNORECASE | re.DOTALL):
            row_html = r.group(1)
            cells = re.findall(
                r'<t[dh]\b[^>]*>(.*?)</t[dh]>', row_html, flags=re.IGNORECASE | re.DOTALL)
            if not cells:
                continue
            rows.append([_strip_html_tags(c) for c in cells])
        if rows:
            tables.append(rows)
    return tables

# -------------------------------
# Core validation logic
# -------------------------------


def _evaluate_table(rows: List[List[str]]) -> Tuple[bool, str]:
    """
    Evaluate a single table (list of rows -> list of cells) for the required components and structure.
    Returns (ok, message) for this table.
    """
    if not rows:
        return False, "Empty table detected."

    # Heuristically determine header presence: if first row contains general words like 'component' and 'value'
    header_candidates = [_normalize_text(c) for c in rows[0]]
    has_header = any('component' in c for c in header_candidates) and any(
        'value' in c for c in header_candidates)

    data_rows = rows[1:] if has_header else rows[:]

    # We require at least two columns
    if any(len(r) < 2 for r in data_rows):
        return False, "Each row must have at least two columns (Component and Value). Ensure you separate columns with '|' (Markdown) or <td> cells (HTML)."

    # Map component name (first column) -> value (second column)
    comp_to_value: dict = {}
    for r in data_rows:
        comp = _normalize_text(r[0])
        val = r[1].strip()
        if comp:
            # Record only first occurrence
            comp_to_value.setdefault(comp, val)

    # Required components
    targets = {
        'theater seating capacity': None,
        'number of ocean species': None,
        # For sum: accept "sum (x + y)" or any label that includes "sum"
        'sum': None
    }

    # Find matches
    found = {
        'theater seating capacity': None,
        'number of ocean species': None,
        'sum': None
    }

    for comp_norm, val in comp_to_value.items():
        if comp_norm == 'theater seating capacity':
            found['theater seating capacity'] = val
        if comp_norm == 'number of ocean species':
            found['number of ocean species'] = val
        # Sum row flexible: match if contains 'sum'
        if 'sum' in comp_norm:
            # Prefer exact "sum (x + y)" if present
            if comp_norm == 'sum (x + y)' or comp_norm.startswith('sum (') or found['sum'] is None:
                found['sum'] = val

    missing = [k for k, v in found.items() if v is None]
    if missing:
        return False, (
            "The table is missing required component rows: "
            + ", ".join(missing)
            + ". Add distinct rows for 'Theater Seating Capacity', 'Number of Ocean Species', and a 'Sum (X + Y)' row."
        )

    # Validate values: must be numeric or explicit unknown markers
    bad_values: List[str] = []
    for label, val in found.items():
        if not _looks_numeric_or_unknown(val):
            bad_values.append(label)

    if bad_values:
        return False, (
            "The following rows have invalid Value cells: "
            + ", ".join(bad_values)
            + ". Each Value must be a number (e.g., 1200) or an explicit unknown marker (e.g., 'Unavailable')."
        )

    # All checks passed for this table
    return True, "Valid tabular format detected with required rows and acceptable values."


def _find_last_relevant_table(response: str) -> Optional[List[List[str]]]:
    """
    Locate the last table (Markdown or HTML) present in the response.
    Preference order: last Markdown table; if none, last HTML table.
    """
    md_tables = _extract_markdown_tables(response)
    html_tables = _extract_html_tables(response)
    if md_tables:
        return md_tables[-1]
    if html_tables:
        return html_tables[-1]
    return None

# -------------------------------
# Public validator (Format)
# -------------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer is presented in a tabular format, clearly listing:
    - Theater Seating Capacity
    - Number of Ocean Species
    - Sum (X + Y)
    Each must appear as separate rows, with at least two columns (Component and Value).
    Accepts Markdown tables (with pipes) or HTML tables.
    Returns (is_valid, detailed_message).
    """
    if not isinstance(response, str) or not response.strip():
        return False, "Response is empty. Provide a Markdown or HTML table containing the required components and values."

    table = _find_last_relevant_table(response)
    if table is None:
        return False, (
            "No table detected. Provide the final answer as a table. "
            "Recommended Markdown format:\n"
            "Component | Value\n"
            "--- | ---\n"
            "Theater Seating Capacity | 1200\n"
            "Number of Ocean Species | 350\n"
            "Sum (X + Y) | 1550"
        )

    ok, msg = _evaluate_table(table)
    if not ok:
        # Provide corrective guidance including a concise template
        return False, (
            msg
            + " Ensure your final answer includes a two-column table (Component | Value) with the three required rows. "
              "Place the numeric totals or explicit 'Unavailable' markers in the Value column. "
              "Example row labels: 'Theater Seating Capacity', 'Number of Ocean Species', 'Sum (X + Y)'."
        )

    return True, "The response satisfies the required tabular format: it includes the three components as separate rows with appropriate values."

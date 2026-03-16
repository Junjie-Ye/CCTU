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
 If the agent intends to proceed with the solution, the following sequence of tools must be strictly adhered to in the specified order: philanthropy_tracker, founder_association_finder, aquarium_species_identifier, marine_ecosystem_locator, marine_biologist_finder, research_location_identifier, cultural_practice_identifier. Additionally, each unique tool can be used at most once in the solution process. The answer must end with a period to ensure proper sentence closure. The response must contain a table, using rows and columns to clearly present data, with proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information. The length of the response must be between 100 and 200 words to ensure sufficient detail while remaining concise and focused.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', "Ending punctuation (The agent's response must end with a period to ensure proper sentence closure.)")
- idx 3: ('Response', 'Format', "(Response, Format, The agent's response must contain a table, using rows and columns to clearly present data. This includes proper use of headers, consistent column widths, and alignment to enhance clarity and accessibility of the information.)")
"""

import re
from typing import Tuple, List, Optional

# -------------------------------
# Helper utilities for validators
# -------------------------------


def _last_meaningful_char_info(text: str) -> Tuple[Optional[str], int]:
    """
    Return the last non-whitespace character and its index, or (None, -1) if not found.
    """
    i = len(text) - 1
    while i >= 0 and text[i].isspace():
        i -= 1
    if i < 0:
        return None, -1
    return text[i], i


def _ends_with_period_allowing_closers(text: str) -> bool:
    """
    Check if the response ends with a period, allowing trailing closing punctuation like quotes/brackets.
    Acceptable endings include:
      - ... .
      - ... ."
      - ... .’)
    """
    closers = set(')"\']}>»”’)】)')
    i = len(text) - 1
    # Skip trailing whitespace
    while i >= 0 and text[i].isspace():
        i -= 1
    # Skip closing punctuation
    while i >= 0 and text[i] in closers:
        i -= 1
    # Now check for period
    return i >= 0 and text[i] == '.'

# -------------------------------
# Markdown table detection
# -------------------------------


_MD_SEPARATOR_RE = re.compile(r'^\s*\|?\s*(?:[:\-]\s*){3,}[\|\s:!\-]*$')
_MD_HEADER_RULE_RE = re.compile(
    r'^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*(?:\:?-{3,}:?\s*)?\s*$')


def _split_markdown_row(line: str) -> List[str]:
    """
    Split a markdown table row into cells, trimming outer pipes and whitespace.
    """
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    parts = [c.strip() for c in s.split('|')]
    return parts


def _detect_markdown_tables(text: str) -> List[dict]:
    """
    Detect Markdown tables with a header and separator line.
    Returns list of table info dicts with validation details.
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines) - 1:
        header = lines[i]
        # Header must look like a row with at least two pipes
        if header.count('|') >= 2:
            # Find next non-empty line for separator
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines):
                sep = lines[j]
                # Must be a markdown header separator (--- with pipes, optional colons)
                if _MD_HEADER_RULE_RE.match(sep):
                    header_cells = _split_markdown_row(header)
                    sep_cells = _split_markdown_row(sep)
                    # Normalize for case where trailing '|' makes an empty cell
                    # Ensure same column count
                    valid = True
                    errors = []
                    n_cols = len(header_cells)
                    if n_cols < 2:
                        valid = False
                        errors.append(
                            "Markdown table header must contain at least 2 columns.")
                    if len(sep_cells) != n_cols:
                        valid = False
                        errors.append(
                            f"Header and separator column counts differ ({n_cols} vs {len(sep_cells)}).")
                    # Collect data rows
                    data_rows = []
                    k = j + 1
                    while k < len(lines):
                        row = lines[k]
                        if row.strip() == '':
                            break
                        if '|' not in row:
                            break
                        data_cells = _split_markdown_row(row)
                        # Allow rows with fewer separators by padding? No, enforce consistency.
                        if len(data_cells) != n_cols:
                            valid = False
                            errors.append(
                                f"Row {k - i} has {len(data_cells)} columns; expected {n_cols}.")
                        data_rows.append(data_cells)
                        k += 1
                    if len(data_rows) == 0:
                        valid = False
                        errors.append(
                            "Markdown table must include at least one data row beneath the header.")
                    table_info = {
                        "type": "markdown",
                        "start_line": i,
                        "end_line": k - 1 if len(lines) > 0 else i,
                        "columns": n_cols,
                        "valid": valid,
                        "errors": errors
                    }
                    tables.append(table_info)
                    i = k
                    continue
        i += 1
    return tables

# -------------------------------
# ASCII table detection
# -------------------------------


_ASCII_BORDER_RE = re.compile(r'^\s*\+(?:-+\+)+\s*$')
_ASCII_ROW_RE = re.compile(r'^\s*\|(?:[^|]*\|)+\s*$')


def _dash_segments(line: str) -> List[int]:
    """
    Get list of dash-run lengths between '+' in an ASCII border line.
    Example: +-----+---+ => [5,3]
    """
    segments = []
    # Extract between '+'
    parts = line.strip().split('+')
    # parts like ['', '-----', '---', '']
    for seg in parts[1:-1]:
        segments.append(len(seg))
    return segments


def _split_ascii_row_cells(line: str) -> List[str]:
    """
    Split ASCII table row into cells by '|', trimming leading/trailing '|' and whitespace.
    """
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c for c in s.split('|')]


def _detect_ascii_tables(text: str) -> List[dict]:
    """
    Detect ASCII tables with +---+ borders and | rows.
    Validates consistent column counts and consistent border segment widths.
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        if _ASCII_BORDER_RE.match(lines[i] or ''):
            # Start of a table candidate
            border_segments = _dash_segments(lines[i])
            n_cols = len(border_segments)
            row_count = 0
            valid = True
            errors = []
            segment_ref = border_segments
            k = i + 1
            saw_row = False
            while k < len(lines):
                line = lines[k]
                if _ASCII_ROW_RE.match(line or ''):
                    cells = _split_ascii_row_cells(line)
                    # Ensure trailing split yields correct count; cells count should be n_cols
                    if len(cells) != n_cols:
                        valid = False
                        errors.append(
                            f"Row at line {k+1} has {len(cells)} columns; expected {n_cols}.")
                    saw_row = True
                    row_count += 1
                    k += 1
                elif _ASCII_BORDER_RE.match(line or ''):
                    # verify border segment widths stay the same across borders
                    segs = _dash_segments(line)
                    if segs != segment_ref:
                        valid = False
                        errors.append(
                            "Border segment widths are inconsistent across the table.")
                    k += 1
                    # Continue until border-row-border pattern ends; if next is not a row, we end
                    if k < len(lines) and not _ASCII_ROW_RE.match(lines[k] or ''):
                        break
                else:
                    break
            if not saw_row:
                valid = False
                errors.append(
                    "ASCII table must have at least one row between border lines.")
            table_info = {
                "type": "ascii",
                "start_line": i,
                "end_line": k - 1 if k > i else i,
                "columns": n_cols,
                "valid": valid,
                "errors": errors
            }
            tables.append(table_info)
            i = k
            continue
        i += 1
    return tables

# -------------------------------
# HTML table detection
# -------------------------------


_HTML_TABLE_RE = re.compile(
    r'<table\b[^>]*>(.*?)</table>', re.IGNORECASE | re.DOTALL)
_HTML_TR_RE = re.compile(r'<tr\b[^>]*>(.*?)</tr>', re.IGNORECASE | re.DOTALL)
_HTML_CELL_RE = re.compile(r'<t[hd]\b[^>]*>', re.IGNORECASE)


def _detect_html_tables(text: str) -> List[dict]:
    """
    Detect HTML tables. Validate presence of headers (<th>) and consistent column counts.
    """
    tables = []
    for m in _HTML_TABLE_RE.finditer(text):
        table_html = m.group(1)
        has_th = bool(re.search(r'<th\b', table_html, re.IGNORECASE))
        rows = _HTML_TR_RE.findall(table_html)
        errors = []
        valid = True
        col_counts = []
        for r in rows:
            cols = _HTML_CELL_RE.findall(r)
            if cols:
                col_counts.append(len(cols))
        if not col_counts:
            valid = False
            errors.append(
                "HTML table must include at least one row with <td> or <th> cells.")
        else:
            expected = col_counts[0]
            for idx, c in enumerate(col_counts[1:], start=2):
                if c != expected:
                    valid = False
                    errors.append(
                        f"Row {idx} has {c} cells; expected {expected}.")
        if not has_th:
            valid = False
            errors.append(
                "HTML table must include header cells using <th> (or a <thead> section).")
        tables.append({
            "type": "html",
            "start_index": m.start(),
            "end_index": m.end(),
            "columns": col_counts[0] if col_counts else 0,
            "valid": valid,
            "errors": errors
        })
    return tables


def _strip_terminal_period_for_format(text: str) -> str:
    """
    For table detection only: remove the final sentence-ending period '.'
    (optionally followed by closing quotes/brackets), so that patterns like
    '| ... |.' won't break table parsing. Do NOT use this for punctuation validation.
    """
    if not text:
        return text

    # keep consistent with punctuation logic if desired
    closers = set(')"\']}>»”’)】')

    # Strip trailing whitespace (but remember it)
    end_ws_len = 0
    i = len(text) - 1
    while i >= 0 and text[i].isspace():
        end_ws_len += 1
        i -= 1
    if i < 0:
        return text

    # Skip closing punctuation (for cases like .") etc.)
    j = i
    while j >= 0 and text[j] in closers:
        j -= 1

    # If the last meaningful punctuation is a period, remove it
    if j >= 0 and text[j] == '.':
        # remove that '.' at position j, keep the rest (including closers and trailing ws)
        return text[:j] + text[j+1:]

    return text

# -------------------------------
# Public Validators
# -------------------------------


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period to ensure proper sentence closure.
    Accepts a period optionally followed by closing quotes/brackets.
    """
    if not response or response.strip() == "":
        return (False, "The response is empty. Ensure the final non-whitespace character is a period ('.'). Add content and end the last sentence with a single period.")
    if _ends_with_period_allowing_closers(response):
        return (True, "Valid: The response ends with a period as required. No changes needed.")
    else:
        return (
            False,
            "Invalid: The response does not end with a period. Ensure the final non-whitespace character (after any closing quotes/brackets) is a '.'. "
            "Fix by adding exactly one period at the end without appending extra text or punctuation. Example: '...final sentence.'."
        )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a clear table with rows and columns,
    proper headers, and consistent structure. Supports:
      - Markdown tables (header row + separator like |---|---|)
      - ASCII tables (+---+---+ borders with | rows)
      - HTML tables (<table> with <th> headers)
    """
    response = _strip_terminal_period_for_format(response)
    # Try Markdown
    md_tables = _detect_markdown_tables(response)
    for t in md_tables:
        if t["valid"]:
            return (True, "Valid: A well-formed Markdown table with a header and consistent columns was detected. Keep column counts consistent across all rows.")
    # If any markdown tables but invalid, collect errors for feedback
    md_errors = []
    for t in md_tables:
        if not t["valid"]:
            md_errors.extend(t["errors"])

    # Try ASCII
    ascii_tables = _detect_ascii_tables(response)
    for t in ascii_tables:
        if t["valid"]:
            return (True, "Valid: A well-formed ASCII table with consistent column widths and structure was detected. No changes needed.")
    ascii_errors = []
    for t in ascii_tables:
        if not t["valid"]:
            ascii_errors.extend(t["errors"])

    # Try HTML
    html_tables = _detect_html_tables(response)
    for t in html_tables:
        if t["valid"]:
            return (True, "Valid: A well-formed HTML table with header cells (<th>) and consistent column counts was detected.")
    html_errors = []
    for t in html_tables:
        if not t["valid"]:
            html_errors.extend(t["errors"])

    # No valid table found; craft detailed guidance
    error_details = []
    if md_errors:
        error_details.append("Markdown issues: " +
                             "; ".join(sorted(set(md_errors))))
    if ascii_errors:
        error_details.append("ASCII table issues: " +
                             "; ".join(sorted(set(ascii_errors))))
    if html_errors:
        error_details.append("HTML table issues: " +
                             "; ".join(sorted(set(html_errors))))

    base_msg = (
        "Invalid: No valid table was detected. Include exactly one clearly formatted table using one of the supported formats:\n"
        "- Markdown: Provide a header row, a separator line (e.g., |---|---|), and data rows with matching column counts.\n"
        "- ASCII: Use +---+ borders and | rows; keep the same number of columns and consistent border segment widths.\n"
        "- HTML: Use <table> with header cells (<th>) and ensure each row has the same number of cells.\n"
    )
    examples = (
        "Examples:\n"
        "Markdown:\n"
        "| Column A | Column B |\n"
        "|---------:|:--------:|\n"
        "| value 1  | value 2  |\n"
        "\nASCII:\n"
        "+----------+----------+\n"
        "| Column A | Column B |\n"
        "+----------+----------+\n"
        "| value 1  | value 2  |\n"
        "+----------+----------+\n"
        "\nHTML:\n"
        "<table><thead><tr><th>Column A</th><th>Column B</th></tr></thead>\n"
        "<tbody><tr><td>value 1</td><td>value 2</td></tr></tbody></table>"
    )

    if error_details:
        return (False, base_msg + "Detected problems: " + " | ".join(error_details) + "\n" + examples)
    else:
        return (False, base_msg + examples)

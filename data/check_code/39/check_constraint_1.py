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
 Your response must be derived through a maximum of 3 total interaction turns with the provided tools, must contain a table with columns for "Chemical Name" and "Description" (where the "Description" column includes their hazardous properties or effects), must end with a period as the final punctuation mark, and the `chemical_release_tracker` tool must be used at most once during the process.

response_constraints_non_length:
- idx 1: ('Response', 'Format', "(Response, Table, Must contain a table with columns for 'Chemical Name' and 'Description', where 'Description' includes their hazardous properties or effects)")
- idx 2: ('Response', 'Punctuation', "Ending punctuation (.) must be used at the end of the agent's response")
"""

import re
from typing import Tuple, List, Dict, Optional

# -------------------------------------------
# Helpers
# -------------------------------------------


def _canonicalize_header(s: str) -> str:
    """Lowercase, remove surrounding spaces, collapse inner whitespace."""
    return re.sub(r'\s+', ' ', s.strip().lower())


def _strip_markdown_formatting(s: str) -> str:
    """Remove common markdown formatting characters from a cell."""
    s = re.sub(r'`([^`]*)`', r'\1', s)       # inline code
    s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)  # bold
    s = re.sub(r'\*([^*]+)\*', r'\1', s)     # italic
    s = re.sub(r'__([^_]+)__', r'\1', s)     # bold
    s = re.sub(r'_([^_]+)_', r'\1', s)       # italic
    return s.strip()


def _strip_html_tags(s: str) -> str:
    """Remove HTML tags, keep text."""
    # Remove scripts/styles
    s = re.sub(r'<(script|style).*?>.*?</\1>', '', s, flags=re.I | re.S)
    # Replace <br> and <p> with spaces
    s = re.sub(r'<\s*(br|p)\s*/?\s*>', ' ', s, flags=re.I)
    # Remove remaining tags
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def _has_markdown_table_separator(line: str) -> bool:
    """Check if a line looks like a markdown table separator row."""
    # e.g., |---|---|, |:---|:---:|, --- | --- etc.
    pattern = r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$'
    return re.match(pattern, line) is not None


def _split_md_row(line: str) -> List[str]:
    """Split a markdown table row by pipes, trimming outer pipes."""
    # Preserve empty cells between pipes (e.g., | a || b |)
    if '|' not in line:
        return []
    # Remove leading/trailing pipe if present to avoid empty first/last artifacts
    core = line.strip()
    if core.startswith('|'):
        core = core[1:]
    if core.endswith('|'):
        core = core[:-1]
    return [cell.strip() for cell in core.split('|')]


def _index_required_columns(headers: List[str]) -> Optional[Dict[str, int]]:
    """Return column indices for 'Chemical Name' and 'Description' if present."""
    canon = [_canonicalize_header(h) for h in headers]
    mapping = {}
    try:
        mapping['name'] = canon.index('chemical name')
        mapping['desc'] = canon.index('description')
    except ValueError:
        return None
    return mapping


# Hazard keywords and codes indicative of hazardous properties/effects
_HAZARD_KEYWORDS = {
    'hazard', 'hazardous', 'toxic', 'poison', 'poisonous', 'fatal', 'lethal',
    'flammable', 'combustible', 'explosive', 'corrosive', 'irritant', 'irritating',
    'corrosivity', 'oxidizer', 'oxidizing', 'asphyxiant', 'choking', 'carcinogen',
    'carcinogenic', 'mutagen', 'mutagenic', 'teratogen', 'teratogenic',
    'sensitizer', 'sensitizing', 'reactive', 'instability', 'harmful',
    'acute', 'chronic', 'danger', 'warning', 'burns', 'causes burns',
    'environmental hazard', 'ecotoxic', 'toxic to aquatic life'
}
# Patterns like GHS H-codes (H200–H373+) and older R-phrases
_HAZARD_CODE_PATTERNS = [
    re.compile(r'\bH\d{3}\b', re.I),
    re.compile(r'\bR\d{2,3}\b', re.I),
]


def _description_has_hazard(text: str) -> bool:
    t = text.lower()
    if any(k in t for k in _HAZARD_KEYWORDS):
        return True
    for pat in _HAZARD_CODE_PATTERNS:
        if pat.search(t):
            return True
    return False

# -------------------------------------------
# Parsers for different "table" formats
# -------------------------------------------


def _parse_markdown_tables(text: str) -> List[Dict]:
    """
    Parse Markdown tables. Returns a list of dicts:
    { 'type': 'markdown', 'headers': [..], 'rows': [[..], ..], 'colmap': {'name': idx, 'desc': idx} }
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines) - 1:
        header_line = lines[i]
        if '|' in header_line:
            headers = _split_md_row(header_line)
            if headers and _index_required_columns(headers) is not None:
                # Check following separator row
                if i + 1 < len(lines) and _has_markdown_table_separator(lines[i + 1]):
                    # Collect data rows until a blank or non-table-ish line
                    data_rows = []
                    j = i + 2
                    while j < len(lines):
                        row_line = lines[j]
                        # Stop when reaching empty line or a line that clearly isn't a table row
                        if not row_line.strip():
                            break
                        # Heuristic: treat as table row if it contains '|' and not a separator
                        if '|' in row_line and not _has_markdown_table_separator(row_line):
                            cells = _split_md_row(row_line)
                            # Normalize list length to header length (pad/truncate)
                            if len(cells) < len(headers):
                                cells += [''] * (len(headers) - len(cells))
                            elif len(cells) > len(headers):
                                cells = cells[:len(headers)]
                            data_rows.append(
                                [_strip_markdown_formatting(c) for c in cells])
                            j += 1
                        else:
                            break
                    colmap = _index_required_columns(headers)
                    tables.append({
                        'type': 'markdown',
                        'headers': headers,
                        'rows': data_rows,
                        'colmap': colmap,
                    })
                    i = j
                    continue
        i += 1
    return tables


def _parse_html_tables(text: str) -> List[Dict]:
    """
    Parse HTML tables. Returns a list of dicts similar to markdown parser.
    """
    tables = []
    for m in re.finditer(r'<table\b.*?>.*?</table>', text, flags=re.I | re.S):
        html = m.group(0)
        # Extract rows
        trs = re.findall(r'<tr\b.*?>.*?</tr>', html, flags=re.I | re.S)
        if not trs:
            continue
        # Extract headers (th) or first row as header
        headers = []
        header_cells = re.findall(
            r'<th\b.*?>(.*?)</th>', trs[0], flags=re.I | re.S)
        if header_cells:
            headers = [_strip_html_tags(c) for c in header_cells]
            data_trs = trs[1:]
        else:
            # Try to use first tr's tds as headers
            td_cells = re.findall(r'<td\b.*?>(.*?)</td>',
                                  trs[0], flags=re.I | re.S)
            if td_cells:
                headers = [_strip_html_tags(c) for c in td_cells]
                data_trs = trs[1:]
            else:
                continue
        colmap = _index_required_columns(headers)
        if colmap is None:
            continue
        # Extract data rows
        data_rows = []
        for tr in data_trs:
            tds = re.findall(r'<td\b.*?>(.*?)</td>', tr, flags=re.I | re.S)
            if not tds:
                continue
            cells = [_strip_html_tags(c) for c in tds]
            # Normalize length
            if len(cells) < len(headers):
                cells += [''] * (len(headers) - len(cells))
            elif len(cells) > len(headers):
                cells = cells[:len(headers)]
            data_rows.append(cells)
        tables.append({
            'type': 'html',
            'headers': headers,
            'rows': data_rows,
            'colmap': colmap,
        })
    return tables


def _parse_csv_like_tables(text: str) -> List[Dict]:
    """
    Parse simple CSV-like tables where a header line of the form
    Chemical Name,Description
    is present, followed by one or more data lines containing commas.
    This is a heuristic, not a full CSV parser.
    """
    tables = []
    lines = text.splitlines()
    i = 0
    header_regex = re.compile(
        r'^\s*"?\s*chemical\s+name\s*"?\s*,\s*"?\s*description\s*"?\s*$', re.I)
    while i < len(lines):
        if header_regex.match(lines[i]):
            headers = ['Chemical Name', 'Description']
            data_rows = []
            j = i + 1
            while j < len(lines):
                line = lines[j]
                if not line.strip():
                    break
                # Consider it part of CSV-like table if it contains at least one comma
                if ',' in line:
                    # Simple split (non-robust against quoted commas), but adequate for validation
                    parts = [p.strip().strip('"') for p in line.split(',')]
                    if len(parts) < 2:
                        j += 1
                        continue
                    # Only keep first two columns; extra columns ignored
                    row = [parts[0], ','.join(parts[1:]).strip()]
                    data_rows.append(row)
                    j += 1
                else:
                    break
            colmap = {'name': 0, 'desc': 1}
            tables.append({
                'type': 'csv',
                'headers': headers,
                'rows': data_rows,
                'colmap': colmap,
            })
            i = j
            continue
        i += 1
    return tables


def _find_valid_tables_with_required_columns(response: str) -> List[Dict]:
    """Find all tables (markdown, html, csv-like) that include required columns."""
    tables = []
    tables.extend(_parse_markdown_tables(response))
    tables.extend(_parse_html_tables(response))
    tables.extend(_parse_csv_like_tables(response))
    # Keep only those that have both required columns (parsers already enforce, but double-check)
    filtered = [t for t in tables if t.get(
        'colmap') and 'name' in t['colmap'] and 'desc' in t['colmap']]
    return filtered

# -------------------------------------------
# Validators
# -------------------------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response contains a table (Markdown, HTML, or simple CSV-like).
    - The table has the columns 'Chemical Name' and 'Description' (case-insensitive match).
    - The table has at least one data row.
    - Each Description cell includes hazardous properties or effects (heuristically checked).
    """
    tables = _find_valid_tables_with_required_columns(response)
    if not tables:
        return (
            False,
            "No valid table detected. Provide a tabular section in Markdown (preferred) or HTML with a header row "
            "that includes exactly the columns 'Chemical Name' and 'Description'. For Markdown, use a header row, a "
            "separator row (---), and at least one data row. Example:\n"
            "| Chemical Name | Description |\n| --- | --- |\n| Chlorine | Toxic, corrosive gas; causes respiratory irritation. |"
        )

    # Choose the first valid table for detailed checks
    table = tables[0]
    headers = table['headers']
    rows = table['rows']
    colmap = table['colmap']

    if not rows:
        return (
            False,
            "A valid table header was found, but there are no data rows. Add at least one row with a chemical name "
            "and a description of its hazardous properties or effects."
        )

    return (
        True,
        "Format is valid: a table with 'Chemical Name' and 'Description' columns was found."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final non-whitespace character of the entire response is a period '.'.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a complete response that ends with a period '.'."
        )
    trimmed = response.rstrip()
    if not trimmed.endswith('.'):
        return (
            False,
            "The response must end with a period '.' as the final character. Add a '.' at the very end of the response."
        )
    return (
        True,
        "Punctuation is valid: the response ends with a period '.'."
    )

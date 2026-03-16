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
 Your response must include bullet points or similar formatting to clearly separate the elevation information for each volcano, must end with a period to ensure proper sentence closure, and must present the elevation data in a tabular format with two columns: 'Volcano Name' and 'Elevation (meters)'.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'The response must include bullet points or similar formatting to clearly separate the elevation information for each volcano.')
- idx 1: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
- idx 2: ('Response', 'Format', "The response must present the elevation data in a tabular format with two columns: 'Volcano Name' and 'Elevation (meters)'.")
"""

import re
from typing import Tuple, List, Optional

# Helper functions for parsing and validation


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1].strip()
    return s


def _normalize(s: str) -> str:
    return re.sub(r'\s+', ' ', _strip_quotes(s)).strip().lower()


def _headers_match(required: List[str], headers: List[str]) -> bool:
    if len(headers) != 2:
        return False
    return _normalize(headers[0]) == _normalize(required[0]) and _normalize(headers[1]) == _normalize(required[1])


def _split_pipe_row(line: str) -> List[str]:
    # Split a pipe row while tolerating optional leading/trailing pipes
    parts = [p.strip() for p in line.split('|')]
    # Remove empty leading/trailing cells created by leading/trailing pipes
    if parts and parts[0] == '':
        parts = parts[1:]
    if parts and parts[-1] == '':
        parts = parts[:-1]
    return parts


def _is_alignment_line(line: str) -> bool:
    # Markdown alignment line like: | --- | :---: |
    line = line.strip()
    if '|' not in line:
        return False
    cells = _split_pipe_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r':?-{3,}:?', c.replace(' ', '')) for c in cells)


def _extract_number(text: str) -> Optional[float]:
    # Find a numeric token (supports commas and decimals)
    m = re.search(r'[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?', text)
    if not m:
        return None
    num = m.group(0).replace(',', '')
    try:
        return float(num)
    except ValueError:
        return None


def _find_bullet_items(response: str) -> List[str]:
    # Recognize bullets: -, *, +, •, –, —, numbered (1., 1), a., a), etc.
    pattern = re.compile(
        r'^\s*(?:[-*+•–—]|[0-9]+[.)]|[A-Za-z][.)])\s+(.+)$', re.MULTILINE)
    return [m.group(1).strip() for m in pattern.finditer(response)]


def _parse_table_from_pipes(lines: List[str]) -> Optional[dict]:
    header_regex = re.compile(
        r'volcano name\s*\|\s*elevation\s*\(meters\)', re.IGNORECASE)
    for i, line in enumerate(lines):
        if '|' in line and header_regex.search(line):
            headers = _split_pipe_row(line)
            # If next line is alignment, skip it
            j = i + 1
            if j < len(lines) and _is_alignment_line(lines[j]):
                j += 1
            rows = []
            while j < len(lines) and '|' in lines[j]:
                row = _split_pipe_row(lines[j])
                if len(row) == 2 and (row[0].strip() or row[1].strip()):
                    rows.append([row[0].strip(), row[1].strip()])
                j += 1
            if headers and len(headers) >= 2:
                headers = [headers[0], headers[1]]
            else:
                continue
            return {'headers': headers, 'rows': rows, 'format': 'pipe'}
    return None


def _parse_table_from_csv(lines: List[str]) -> Optional[dict]:
    header_regex = re.compile(
        r'^\s*volcano name\s*,\s*elevation\s*\(meters\)\s*$', re.IGNORECASE)
    for i, line in enumerate(lines):
        if header_regex.match(line):
            headers = [h.strip()
                       for h in re.split(r'\s*,\s*', line, maxsplit=1)]
            rows = []
            j = i + 1
            while j < len(lines) and ',' in lines[j]:
                parts = [p.strip()
                         for p in re.split(r'\s*,\s*', lines[j], maxsplit=1)]
                if len(parts) == 2 and (parts[0] or parts[1]):
                    rows.append(parts)
                j += 1
            return {'headers': headers, 'rows': rows, 'format': 'csv'}
    return None


def _parse_table_from_tsv(lines: List[str]) -> Optional[dict]:
    header_regex = re.compile(
        r'^\s*volcano name\s*\t\s*elevation\s*\(meters\)\s*$', re.IGNORECASE)
    for i, line in enumerate(lines):
        if header_regex.match(line):
            headers = [h.strip() for h in line.split('\t')]
            rows = []
            j = i + 1
            while j < len(lines) and '\t' in lines[j]:
                parts = [p.strip() for p in lines[j].split('\t')]
                if len(parts) >= 2:
                    rows.append([parts[0], parts[1]])
                j += 1
            return {'headers': headers[:2], 'rows': rows, 'format': 'tsv'}
    return None


def _parse_table_from_spaces(lines: List[str]) -> Optional[dict]:
    header_regex = re.compile(
        r'^\s*volcano name\s{2,}elevation\s*\(meters\)\s*$', re.IGNORECASE)
    for i, line in enumerate(lines):
        if header_regex.match(line):
            headers = [h.strip()
                       for h in re.split(r'\s{2,}', line, maxsplit=1)]
            rows = []
            j = i + 1
            while j < len(lines):
                if re.search(r'\s{2,}', lines[j]):
                    parts = [p.strip() for p in re.split(
                        r'\s{2,}', lines[j], maxsplit=1)]
                    if len(parts) == 2 and (parts[0] or parts[1]):
                        rows.append(parts)
                        j += 1
                    else:
                        break
                else:
                    break
            return {'headers': headers, 'rows': rows, 'format': 'space'}
    return None


def _parse_elevation_table(response: str) -> Optional[dict]:
    """
    Try to find a table with exactly two columns:
    'Volcano Name' and 'Elevation (meters)' in common formats (Markdown/pipe, CSV, TSV, space-separated).
    Returns dict with keys: headers (List[str]), rows (List[List[str]]), format (str), or None if not found.
    """
    lines = response.strip().splitlines()
    parsers = [
        _parse_table_from_pipes,
        _parse_table_from_csv,
        _parse_table_from_tsv,
        _parse_table_from_spaces,
    ]
    for parser in parsers:
        table = parser(lines)
        if table is not None:
            return table
    return None


def _validate_numeric_elevations(rows: List[List[str]]) -> Tuple[bool, List[int]]:
    """
    Check that each row's second column contains a numeric elevation.
    Returns (ok, bad_indices)
    """
    bad = []
    for idx, row in enumerate(rows):
        if len(row) < 2:
            bad.append(idx)
            continue
        num = _extract_number(row[1])
        if num is None:
            bad.append(idx)
    return (len(bad) == 0, bad)

# Validators to generate


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response presents the elevation data in a tabular format
    with exactly two columns: 'Volcano Name' and 'Elevation (meters)'.
    Acceptable formats include Markdown pipe tables, CSV, TSV, or space-aligned tables.
    """
    table = _parse_elevation_table(response)
    required_headers = ["Volcano Name", "Elevation (meters)"]

    if table is None:
        return (
            False,
            "No valid table was found. Add a table with exactly two columns titled 'Volcano Name' and 'Elevation (meters)'. "
            "You may use Markdown pipes (|), CSV (comma-separated), TSV (tab-separated), or space-aligned columns. "
            "Include at least one data row under these headers."
        )

    headers = table['headers']
    if not _headers_match(required_headers, headers):
        return (
            False,
            f"Header mismatch. Found headers: {headers}. The table must have exactly two columns titled "
            "'Volcano Name' and 'Elevation (meters)' (case-insensitive, quotes allowed). "
            "Update the header row to match these titles."
        )

    rows = table['rows']
    if not rows:
        return (
            False,
            "The table contains no data rows. Add at least one row with a volcano name in the first column "
            "and its elevation (meters) in the second column."
        )

    for i, row in enumerate(rows):
        if len(row) != 2:
            return (
                False,
                f"Row {i+1} does not have exactly two cells. Ensure every data row has two columns: "
                "first column for the volcano name and second column for the elevation (meters)."
            )

    ok_numeric, bad_rows = _validate_numeric_elevations(rows)
    if not ok_numeric:
        readable = ", ".join(str(i + 1) for i in bad_rows)
        return (
            False,
            f"Non-numeric elevation detected in row(s): {readable}. Ensure the 'Elevation (meters)' column contains "
            "numeric values (e.g., 1325 or 1,325). Avoid units in the cell; meters are implied by the header."
        )

    return (
        True,
        "Valid table format detected with headers 'Volcano Name' and 'Elevation (meters)', at least one data row, "
        "and numeric elevations in the second column."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period.
    """
    trimmed = response.rstrip()
    if not trimmed.endswith('.'):
        return (
            False,
            "The final character of the response is not a period. Append a '.' at the very end of the response "
            "(after any tables or bullet points) to satisfy the punctuation requirement."
        )
    return (
        True,
        "The response ends with a period."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes bullet points or similar formatting
    to clearly separate the elevation information for each volcano.
    """
    bullets = _find_bullet_items(response)
    table = _parse_elevation_table(response)
    volcano_count = len(table['rows']) if table else 0
    volcano_names = [row[0].strip() for row in table['rows']] if table else []

    if not bullets:
        return (
            False,
            "No bullet points or enumerated items were found. Add a bullet list or numbered list that clearly separates "
            "each volcano's elevation entry. For example:\n"
            "- Mount Example — 1,234 m\n"
            "- Volcano Beta — 2,345 m\n"
            "Use markers like '- ', '* ', '• ', '1. ', or '1)' at the start of each line."
        )

    # If we have a table, align bullets with table rows
    if volcano_count > 0:
        if len(bullets) < volcano_count:
            return (
                False,
                f"Insufficient bullet items: found {len(bullets)} but the table lists {volcano_count} volcano(es). "
                "Provide one bullet item per volcano so readers can see each entry clearly separated."
            )

        # Check each volcano name appears in at least one bullet
        matched = 0
        lower_bullets = [b.lower() for b in bullets]
        for name in volcano_names:
            name_low = name.lower()
            if any(name_low in b for b in lower_bullets):
                matched += 1

        if matched < volcano_count:
            return (
                False,
                "Bullet items do not consistently include the volcano names. For clarity, include the volcano's name in "
                "each bullet and ensure there is one bullet per table row, e.g., '- Volcano Name — 1,234 m'."
            )

    # Check that bullets include numeric elevation information
    bullets_without_numbers = [i for i, b in enumerate(
        bullets, start=1) if _extract_number(b) is None]
    if bullets_without_numbers:
        idxs = ", ".join(map(str, bullets_without_numbers))
        return (
            False,
            f"Bullet item(s) {idxs} lack numeric elevation values. Include the elevation number in each bullet, "
            "e.g., '- Volcano Name — 1,234 m'."
        )

    return (
        True,
        "Bullet points detected and they include numeric elevation values. If a table is present, ensure one bullet per "
        "volcano row and include the volcano names in each bullet for clarity."
    )

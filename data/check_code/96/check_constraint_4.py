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
 You must complete this task within at most 8 interaction turns with the provided tools, and your final answer must be concise, containing at most 150 words. If the agent initiates the analysis using `urban_area_identifier`, it is strictly required to proceed with the following sequence of tool calls: `business_district_locator` -> `business_locator` -> `consulting_client_finder` -> `corporate_housing_locator` -> `rental_price_analyzer`. Furthermore, you must not invoke any single tool more than 2 times during the task. The final answer must be presented in a tabular format, with at least two columns and two rows, clearly separating the key components of the answer (e.g., "Step" and "Result").

response_constraints_non_length:
- idx 4: ('Response', 'Format', '(Response, Table, The final answer must be presented in a tabular format, with at least two columns and two rows, clearly separating the key components of the answer (e.g., "Step" and "Result").)')
"""

import re
import csv
from io import StringIO
from typing import List, Tuple, Optional


# ---------------------------
# Helpers
# ---------------------------

def _extract_final_answer(text: str) -> str:
    """
    Extract the [FINAL ANSWER] section if present; otherwise return the whole text.
    """
    m = re.search(r'\[FINAL ANSWER\](.*)', text,
                  flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def _parse_markdown_tables(text: str) -> List[dict]:
    """
    Find Markdown tables and return list of dicts:
      {
        'header': List[str],
        'rows': List[List[str]],
        'n_cols': int,
        'n_rows_total': int  # includes header + data (excludes separator row)
      }
    A valid Markdown table requires a header, a separator line (---), and >= 1 data row.
    """
    lines = text.splitlines()
    tables = []

    def split_md_row(line: str) -> List[str]:
        # Remove leading/trailing pipe if present, then split.
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        return [c.strip() for c in line.split('|')]

    sep_pattern = re.compile(r'^\s*\|?\s*:?-{3,}\s*(\|\s*:?-{3,}\s*)+\|?\s*$')

    i = 0
    while i < len(lines) - 1:
        header_line = lines[i]
        sep_line = lines[i + 1]
        if '|' in header_line and sep_pattern.match(sep_line):
            header_cells = split_md_row(header_line)
            if len(header_cells) < 2:
                i += 1
                continue
            # collect data rows
            data_rows = []
            j = i + 2
            while j < len(lines):
                l = lines[j].strip()
                if l and '|' in l and not sep_pattern.match(l):
                    data_rows.append(split_md_row(l))
                    j += 1
                else:
                    break
            # normalize column count by padding/truncation to header length
            data_rows_norm = []
            for r in data_rows:
                if len(r) < len(header_cells):
                    r = r + [''] * (len(header_cells) - len(r))
                elif len(r) > len(header_cells):
                    r = r[:len(header_cells)]
                data_rows_norm.append(r)

            if data_rows_norm:  # at least one data row
                tables.append({
                    'header': header_cells,
                    'rows': data_rows_norm,
                    'n_cols': len(header_cells),
                    'n_rows_total': 1 + len(data_rows_norm)  # header + data
                })
            i = j
        else:
            i += 1
    return tables


def _parse_html_tables(text: str) -> List[dict]:
    """
    Find HTML tables and return list of dicts:
      {
        'header': List[str],   # from <th> if any, else first row <td>
        'rows': List[List[str]],
        'n_cols': int,
        'n_rows_total': int
      }
    """
    tables = []
    for tbl_match in re.finditer(r'<table\b.*?>.*?</table>', text, flags=re.IGNORECASE | re.DOTALL):
        tbl_html = tbl_match.group(0)
        rows_html = re.findall(r'<tr\b.*?>(.*?)</tr>',
                               tbl_html, flags=re.IGNORECASE | re.DOTALL)
        if not rows_html:
            continue

        parsed_rows = []
        header = None

        for idx, row_html in enumerate(rows_html):
            th_cells = re.findall(r'<th\b.*?>(.*?)</th>',
                                  row_html, flags=re.IGNORECASE | re.DOTALL)
            td_cells = re.findall(r'<td\b.*?>(.*?)</td>',
                                  row_html, flags=re.IGNORECASE | re.DOTALL)

            def clean_cell(s: str) -> str:
                # strip tags inside cells
                s = re.sub(r'<.*?>', '', s, flags=re.DOTALL)
                return s.strip()

            if th_cells:
                cells = [clean_cell(c) for c in th_cells]
                if not header:
                    header = cells
                else:
                    parsed_rows.append(cells)
            elif td_cells:
                cells = [clean_cell(c) for c in td_cells]
                parsed_rows.append(cells)

        if header is None and parsed_rows:
            # Use first row as header if no <th> present
            header = parsed_rows[0]
            parsed_rows = parsed_rows[1:]

        if header and len(header) >= 2 and (len(parsed_rows) + 1) >= 2:
            # Normalize row cell counts to header length
            norm_rows = []
            for r in parsed_rows:
                if len(r) < len(header):
                    r = r + [''] * (len(header) - len(r))
                elif len(r) > len(header):
                    r = r[:len(header)]
                norm_rows.append(r)

            tables.append({
                'header': header,
                'rows': norm_rows,
                'n_cols': len(header),
                'n_rows_total': 1 + len(norm_rows)
            })
    return tables


def _parse_csv_tables(text: str) -> List[dict]:
    """
    Try to parse CSV-like tables (comma-separated) in contiguous line blocks.
    Return list of dicts same as others.
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        # Find start of a CSV block: line containing at least one comma
        if ',' in lines[i]:
            block = [lines[i]]
            j = i + 1
            while j < len(lines) and (',' in lines[j]) and lines[j].strip() != '':
                block.append(lines[j])
                j += 1

            # Parse with csv.reader
            reader = csv.reader(StringIO('\n'.join(block)))
            rows = [[c.strip() for c in r]
                    for r in reader if any(c.strip() for c in r)]
            if len(rows) >= 2:
                n_cols = max(len(r) for r in rows)
                # Normalize rows to same column count
                rows = [(r + [''] * (n_cols - len(r))) for r in rows]
                header = rows[0]
                data = rows[1:]
                if len(header) >= 2 and len(rows) >= 2:
                    tables.append({
                        'header': header,
                        'rows': data,
                        'n_cols': n_cols,
                        'n_rows_total': len(rows)  # header + data
                    })
            i = j
        else:
            i += 1
    return tables


def _header_is_clear(header: List[str]) -> bool:
    """
    Check if header has at least two non-empty, non-purely-numeric cells.
    """
    non_empty = [h for h in header if h and not re.fullmatch(r'\s*', h)]
    if len(non_empty) < 2:
        return False
    meaningful = [h for h in non_empty if not re.fullmatch(r'\d+(\.\d+)?', h)]
    return len(meaningful) >= 2


# ---------------------------
# Validators
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer is presented in a tabular format with:
    - at least two columns
    - at least two rows (header counts as one row)
    - clearly separated key components via a header row (e.g., "Step", "Result")
    Recognizes Markdown tables, HTML tables, and CSV-like tables.
    """
    text = _extract_final_answer(response)

    md_tables = _parse_markdown_tables(text)
    html_tables = _parse_html_tables(text)
    csv_tables = _parse_csv_tables(text)

    candidates = md_tables + html_tables + csv_tables

    for t in candidates:
        if t['n_cols'] >= 2 and t['n_rows_total'] >= 2 and _header_is_clear(t['header']):
            return True, (
                "Format OK: Found a valid table with at least two columns and two rows. "
                "Keep a clear header (e.g., 'Step' and 'Result') and ensure all content required by the task "
                "appears inside this table in the [FINAL ANSWER] section only."
            )

    # Build detailed guidance
    details = []
    if not candidates:
        details.append(
            "- No valid table detected. Provide a table using one of: Markdown, HTML, or CSV."
        )
    else:
        for t in candidates:
            if t['n_cols'] < 2:
                details.append(
                    f"- A table was found but has only {t['n_cols']} column(s). Need at least 2.")
            if t['n_rows_total'] < 2:
                details.append(
                    f"- A table was found but has only {t['n_rows_total']} row(s). Need at least 2 (header counts as one).")
            if not _header_is_clear(t['header']):
                details.append(
                    "- Table header is missing or unclear. Use explicit headers like 'Step' and 'Result'.")

    guidance = (
        "Invalid format: The final answer must be a table with at least two columns and two rows, "
        "and a clear header (e.g., 'Step' and 'Result').\n"
        + "\n".join(details) + "\n"
        "Fix by outputting, in the [FINAL ANSWER] section, a self-contained table. For example (Markdown):\n"
        "| Step | Result |\n| --- | --- |\n| Identify tasks | ... |\n| Execute tools | ... |"
    )
    return False, guidance

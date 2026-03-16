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
 The agent must solve this by calling the provided tools, present the final answer in a tabular format with columns for "Species" and "Number of Ventricles" and a row for each species, complete the task in a total number of interaction turns that falls within a range of 2 to 3 (inclusive), and ensure the final response is between 50 and 100 words in length to balance conciseness and detail. All information must be obtained through tool calls, and the agent must analyze and correct any failed tool calls until a successful solution is achieved.

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'Must present the answer in a tabular format with columns for "Species" and "Number of Ventricles" and a row for each species (human and frog).')
"""

import re
from typing import List, Tuple, Optional, Dict

# Helper: normalize header/cell text


def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip().strip('|').strip()).strip().strip('*_`"').strip()


# Helper: is a Markdown separator row like |---|:---:|
_SEP_CELL = re.compile(r'^:?-{3,}:?$')


def _is_md_separator_row(line: str, delim: str) -> bool:
    if delim != '|':
        return False
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cells) < 2:
        return False
    return all(_SEP_CELL.match(c) is not None for c in cells if c != '')

# Helper: split a delimited line into cells, handling Markdown pipe rails


def _split_line(line: str, delim: str) -> List[str]:
    if delim == '|':
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
    parts = [_clean(p) for p in line.split(delim)]
    # Remove pure empty trailing cells potentially created by trailing delimiter
    while parts and parts[-1] == '':
        parts.pop()
    return parts

# Attempt to parse a table starting at a given header line index with a given delimiter


def _parse_table_from_header(lines: List[str], start_idx: int, delim: str) -> Optional[Dict]:
    header_line = lines[start_idx]
    header_cells = _split_line(header_line, delim)
    # Need at least two columns to be a table
    if len(header_cells) < 2:
        return None

    # Collect body lines until a stopping condition
    i = start_idx + 1
    # Skip Markdown separator row if present
    if i < len(lines) and _is_md_separator_row(lines[i], delim):
        i += 1

    rows = []
    while i < len(lines):
        line = lines[i]
        # Stop if blank line
        if not line.strip():
            break
        # Stop if line doesn't look like part of the same delimited block
        if delim not in line:
            # For CSV/tab, also allow continued rows only if they keep the same number of delimiters
            if delim in [',', '\t']:
                pass  # handled by above check; if no delim, break
            break
        row_cells = _split_line(line, delim)
        # If the row has fewer cells than headers, we still keep but pad (we only need mapped columns)
        if any(cell != '' for cell in row_cells):
            rows.append(row_cells)
        i += 1

    if not rows:
        return None

    return {
        'headers': header_cells,
        'rows': rows,
        'end_idx': i
    }

# Extract candidate tables by scanning for header lines that include both required headers


def _extract_tables(text: str) -> List[Dict]:
    lines = text.splitlines()
    tables = []
    required_headers = {'species', 'number of ventricles'}
    delimiters = ['|', ',', '\t']
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        for delim in delimiters:
            if delim not in line:
                continue
            header_cells = _split_line(line, delim)
            header_norm = [_clean(c).lower() for c in header_cells]
            if required_headers.issubset(set(header_norm)):
                parsed = _parse_table_from_header(lines, idx, delim)
                if parsed is not None:
                    parsed['delim'] = delim
                    tables.append(parsed)
    return tables

# Map headers to column indices (case-insensitive)


def _map_header_indices(headers: List[str]) -> Dict[str, int]:
    mapping = {}
    for i, h in enumerate(headers):
        key = _clean(h).lower()
        mapping[key] = i
    return mapping

# Find rows for human and frog; accepts singular/plural case-insensitive


def _normalize_species_name(name: str) -> str:
    n = _clean(name).lower()
    # Allow plural forms "humans" -> "human", "frogs" -> "frog"
    if n.endswith('s'):
        n = n[:-1]
    return n


def _is_integer_cell(val: str) -> bool:
    return re.fullmatch(r'\d+', _clean(val)) is not None


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response presents the answer in a tabular format with columns
    'Species' and 'Number of Ventricles' and includes a row for Human and a row for Frog.
    Accepts Markdown pipe tables, CSV, or tab-delimited tables anywhere in the response.
    """
    tables = _extract_tables(response)
    if not tables:
        return (
            False,
            "No valid table found. Provide a 2-column table with headers exactly 'Species' and 'Number of Ventricles'. "
            "Use a Markdown table (preferred) like:\n"
            "| Species | Number of Ventricles |\n|---|---|\n| Human | 4 |\n| Frog | 3 |"
        )

    # Evaluate each table; pass if any satisfies constraints
    for t in tables:
        headers = t['headers']
        header_map = _map_header_indices(headers)
        # Require both headers to be present (case-insensitive)
        if 'species' not in header_map or 'number of ventricles' not in header_map:
            continue

        species_idx = header_map['species']
        ventricles_idx = header_map['number of ventricles']

        # Check rows for human and frog presence and numeric ventricles
        found = {'human': False, 'frog': False}
        missing_numeric = False

        for row in t['rows']:
            # Pad row if shorter than headers
            if len(row) <= max(species_idx, ventricles_idx):
                continue
            sp = _normalize_species_name(row[species_idx])
            if sp in ('human', 'frog'):
                if not _is_integer_cell(row[ventricles_idx]):
                    missing_numeric = True
                else:
                    found[sp] = True

        if missing_numeric:
            return (
                False,
                "The 'Number of Ventricles' cells for Human and Frog must be integers (e.g., 4, 3). "
                "Do not include units or words; use digits only."
            )

        if not found['human'] or not found['frog']:
            missing = []
            if not found['human']:
                missing.append('Human')
            if not found['frog']:
                missing.append('Frog')
            return (
                False,
                f"Table is missing required row(s): {', '.join(missing)}. "
                "Ensure there is one row for each species with an integer in 'Number of Ventricles'."
            )

        # Passed all checks for this table
        # Optional gentle guidance to keep only required columns if extras exist
        extra_cols = len(headers) > 2
        if extra_cols:
            return (
                True,
                "Valid table detected with required headers and rows. Consider limiting the table to only two columns: "
                "'Species' and 'Number of Ventricles' for maximal compliance."
            )
        return (
            True,
            "Valid: Found a table with headers 'Species' and 'Number of Ventricles', including rows for Human and Frog with integer values."
        )

    # If we examined tables but none fully passed
    return (
        False,
        "A table was detected, but it does not fully comply. Ensure headers are exactly 'Species' and 'Number of Ventricles' "
        "(case-insensitive), include rows for both Human and Frog, and use integer digits in the ventricles column."
    )

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
 If the agent intends to retrieve data, at least one interaction turn must involve the simultaneous invocation of two unique tool types. The 'historical_event_facts' and 'historical_crime_analyzer' tools may be invoked no more than once each. A maximum of 3 interaction turns is allowed, with a total of at most 2 tool calls across all interaction turns. The final answer must begin with the identifier "Final Answer: " followed by the calculated difference in the number of deaths and contain a table with columns for "Name", "Number of Deaths", and "Difference". The difference must be calculated and displayed as the third row in the table.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'Start identifier (Mandates that the agent\'s response must begin with a specific identifier or phrase, ensuring a consistent and recognizable opening. Specific Constraint: The agent\'s final answer must begin with the identifier "Final Answer: " followed by the calculated difference in the number of deaths.)')
- idx 4: ('Response', 'Format', 'The final answer must contain a table with columns for "Name", "Number of Deaths", and "Difference". The difference must be calculated and displayed as the third row in the table.')
"""

import re
from typing import Tuple, List, Optional
from decimal import Decimal, InvalidOperation

# Helper functions


def _strip_pipes_and_split(line: str) -> List[str]:
    """
    Normalize a table line by removing leading/trailing pipes and splitting into cells.
    """
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_separator_line(line: str) -> bool:
    """
    Check if a line is a typical Markdown table separator (pipes + dashes).
    """
    s = line.strip().replace(" ", "")
    if not s:
        return False
    # Must contain '|' and consist only of '|' and '-' characters.
    return ("|" in s) and all(ch in "-|" for ch in s)


def _find_first_table(response: str) -> Optional[Tuple[List[str], List[List[str]]]]:
    """
    Find and parse the first Markdown-like table in the response.
    Returns (header_cells, row_cells) where:
      - header_cells: list of header cell strings
      - row_cells: list of rows, each row is a list of cell strings aligned to header length
    The function expects rows to start with '|' and be pipe-delimited.
    """
    lines = response.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i].strip()
        # Skip code fences
        if line.startswith("```"):
            # Skip until next fence
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                i += 1
            i += 1
            continue
        if line.startswith("|") and "|" in line:
            header = _strip_pipes_and_split(line)
            # Look for a separator line next
            sep_idx = i + 1
            if sep_idx < n and _is_separator_line(lines[sep_idx]):
                # Collect data rows
                rows: List[List[str]] = []
                j = sep_idx + 1
                while j < n and lines[j].strip().startswith("|"):
                    row_cells = _strip_pipes_and_split(lines[j])
                    # Normalize row length to header length
                    if len(row_cells) < len(header):
                        row_cells += [""] * (len(header) - len(row_cells))
                    elif len(row_cells) > len(header):
                        row_cells = row_cells[:len(header)]
                    rows.append(row_cells)
                    j += 1
                if header and rows:
                    return (header, rows)
                i = j
                continue
            else:
                # Not a valid table (missing separator line), continue scanning
                i += 1
                continue
        i += 1
    return None


def _normalize_header_name(name: str) -> str:
    """
    Normalize header names for matching (case-insensitive, collapse spaces).
    """
    return re.sub(r"\s+", " ", name.strip().lower())


def _parse_number(cell: str) -> Optional[Decimal]:
    """
    Parse a numeric cell into Decimal. Returns None if not a valid number.
    Allows integers or decimals, optionally with leading '+' or '-'.
    """
    s = cell.strip()
    if not s:
        return None
    # Accept commas in thousands formatting by removing them
    s_clean = s.replace(",", "")
    try:
        return Decimal(s_clean)
    except InvalidOperation:
        return None

# Validators


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that:
    - The response begins exactly with the identifier 'Final Answer: ' at the very first character.
    """
    required_prefix = "Final Answer: "
    if not response.startswith(required_prefix):
        return (
            False,
            "Your output must start at the very first character with 'Final Answer: '. "
            "Remove any leading whitespace or text and place the identifier exactly as 'Final Answer: ' "
            "on its own line, followed immediately by the table."
        )
    return (True, "Validation passed: The response begins with the required 'Final Answer: ' identifier.")


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates that:
    - The final answer contains a Markdown-style table.
    - The table includes columns for 'Name', 'Number of Deaths', and 'Difference' (case-insensitive).
    - The computed difference is displayed as the third row:
        * The third row's 'Name' cell must be 'Difference'.
        * The third row's 'Number of Deaths' cell should be empty.
        * The third row's 'Difference' cell must equal X - Y, where X and Y are the first two rows' numbers of deaths.
    """
    table = _find_first_table(response)
    if table is None:
        return (
            False,
            "Include a Markdown table immediately after 'Final Answer: '. The table must have a header row and "
            "a separator line (e.g., '|---|---|---|'), followed by at least three data rows."
        )
    header, rows = table
    if len(rows) < 3:
        return (
            False,
            "The table must contain at least three data rows: the first two for the subjects and the third row for the computed difference."
        )
    # Map required columns
    header_map = {_normalize_header_name(
        h): idx for idx, h in enumerate(header)}
    required_cols = {
        "name": None,
        "number of deaths": None,
        "difference": None
    }
    for key in list(required_cols.keys()):
        idx = header_map.get(key)
        if idx is None:
            return (
                False,
                "The table header must include exactly these columns (case-insensitive): "
                "'Name', 'Number of Deaths', and 'Difference'. Ensure the header row matches these names."
            )
        required_cols[key] = idx

    name_idx = required_cols["name"]  # type: ignore
    num_idx = required_cols["number of deaths"]  # type: ignore
    diff_idx = required_cols["difference"]  # type: ignore

    # Validate first two rows have numeric 'Number of Deaths'
    if len(rows[0]) <= num_idx or len(rows[1]) <= num_idx:
        return (
            False,
            "Ensure the first two rows contain a numeric value in the 'Number of Deaths' column."
        )

    x = _parse_number(rows[0][num_idx])
    y = _parse_number(rows[1][num_idx])
    if x is None or y is None:
        return (
            False,
            "The 'Number of Deaths' cells in the first two rows must be numeric (integers, optionally with thousands separators). "
            "Replace any non-numeric text with valid numbers."
        )

    # Validate third row format and computed difference
    third = rows[2]
    if len(third) <= max(name_idx, num_idx, diff_idx):
        return (
            False,
            "The third row must include cells for 'Name', 'Number of Deaths', and 'Difference'."
        )

    third_name = third[name_idx].strip()
    if _normalize_header_name(third_name) != "difference":
        return (
            False,
            "The third row's 'Name' cell must be 'Difference'. Set the first cell of the third row to 'Difference'."
        )

    # Number of Deaths in third row should be empty
    if third[num_idx].strip() != "":
        return (
            False,
            "Leave the 'Number of Deaths' cell in the third row empty. Move the computed value to the 'Difference' column."
        )

    third_diff_val = _parse_number(third[diff_idx])
    if third_diff_val is None:
        return (
            False,
            "The third row's 'Difference' cell must be a numeric value equal to (X - Y), "
            "where X and Y are the 'Number of Deaths' from the first two rows."
        )

    computed = x - y
    if third_diff_val != computed:
        return (
            False,
            f"The third row's 'Difference' value is incorrect. It must equal (X - Y) = ({x} - {y}) = {computed}. "
            "Update the 'Difference' cell in the third row to this computed value."
        )

    return (True, "Validation passed: The table contains the required columns and the third row correctly shows the computed difference.")

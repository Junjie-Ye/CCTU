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
 You must solve this using the provided tools and cannot rely on internal knowledge. You must not call the 'product_price_checker' function more than 2 times during the process. The total number of interaction turns must fall within a range of 6 to 8 (inclusive). The response must contain a table with two columns: "Product" and "Price (USD)", and the combined price must be clearly indicated in the table. The response must end with a period. If the agent chooses to invoke the 'car_price_analyzer' and 'product_price_comparator' functions, these must be executed concurrently.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', '(Response, Ending punctuation, The response must end with a period.)')
- idx 3: ('Response', 'Format', 'The response must contain a table with two columns: "Product" and "Price (USD)", and the combined price must be clearly indicated in the table.')
"""

import re
from typing import List, Tuple, Optional

# ============================================================
# Helpers for Markdown table parsing and validation
# ============================================================

_MD_SEP_CELL_RE = re.compile(r"^\s*:?-{3,}:?\s*$")

MONEY_RE = re.compile(r"""(?ix)
(?<!\w)
(?:USD\s*)?
\$?\s*
(?:\d+(?:,\d{3})*|\d+)   
(?:\.\d+)?
(?!\w)
""")

COMBINED_LABELS = [
    "total",
    "total price",
    "combined",
    "combined price",
    "sum",
    "grand total",
    "overall",
    "overall total",
]


def _split_md_row(line: str) -> List[str]:
    # Remove leading/trailing pipe and split
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_md_separator_line(line: str, expected_cols: int) -> bool:
    cells = _split_md_row(line)
    if len(cells) < expected_cols:
        return False
    return all(_MD_SEP_CELL_RE.match(c) is not None for c in cells[:expected_cols])


def _parse_markdown_tables(text: str) -> List[Tuple[List[str], List[List[str]]]]:
    """
    Returns a list of tables found in the text.
    Each table is (headers: List[str], rows: List[List[str]]).
    Only GitHub-style pipe tables with a separator line are recognized.
    """
    lines = text.splitlines()
    i = 0
    tables: List[Tuple[List[str], List[List[str]]]] = []

    while i < len(lines) - 1:
        header_candidate = lines[i]
        sep_candidate = lines[i + 1]

        if "|" in header_candidate and "|" in sep_candidate:
            header_cells = _split_md_row(header_candidate)
            col_count = len(header_cells)

            if col_count >= 2 and _is_md_separator_line(sep_candidate, col_count):
                # Collect data rows
                rows: List[List[str]] = []
                j = i + 2
                while j < len(lines):
                    row_line = lines[j]
                    if "|" not in row_line:
                        break
                    row_cells = _split_md_row(row_line)
                    # enforce exactly the same number of columns as header
                    if len(row_cells) != col_count:
                        break
                    rows.append(row_cells)
                    j += 1

                tables.append((header_cells, rows))
                i = j
                continue

        i += 1

    return tables


def _headers_match_exact(headers: List[str]) -> bool:
    if len(headers) != 2:
        return False
    return headers[0] == "Product" and headers[1] == "Price (USD)"


def _find_combined_row(rows: List[List[str]]) -> Optional[List[str]]:
    for r in rows:
        if len(r) != 2:
            continue
        product_cell = r[0].strip().lower()
        for kw in COMBINED_LABELS:
            if kw in product_cell:
                return r
        # Also accept exact header-style phrasing like "Combined price"
        if "combined price" in product_cell:
            return r
    return None


def _has_money_value(cell: str) -> bool:
    return MONEY_RE.search(cell or "") is not None


# ============================================================
# Validators
# ============================================================

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates:
    - The response contains a single table with exactly two columns.
    - The headers are exactly: 'Product' and 'Price (USD)' (case and punctuation must match).
    - The table includes a row indicating the combined price (e.g., 'Total', 'Combined', 'Grand Total').
    - The combined price cell includes a numeric USD amount (e.g., $1,234.56).
    """
    tables = _parse_markdown_tables(response)
    if not tables:
        return (
            False,
            "No valid Markdown table detected. Create a GitHub-style pipe table with a header row, a separator row (---), and data rows. "
            "The table must have exactly two columns with headers exactly 'Product' and 'Price (USD)'. "
            "Include a final row inside the same table (e.g., 'Total' or 'Combined') that shows the combined price in the 'Price (USD)' column."
        )

    for headers, rows in tables:
        # Normalize headers by stripping
        headers = [h.strip() for h in headers]
        # Check exact headers
        if not _headers_match_exact(headers):
            return (
                False,
                "The table headers are incorrect. They must be exactly two columns named 'Product' and 'Price (USD)' in that order. "
                "Match the casing, spacing, and parentheses exactly."
            )
        # Ensure rows have exactly two columns
        for r in rows:
            if len(r) != 2:
                return (
                    False,
                    "Each table row must have exactly two cells to match the headers 'Product' and 'Price (USD)'. "
                    "Remove extra columns or merge cells so that every row has exactly two cells."
                )
        # Combined price row check
        combined_row = _find_combined_row(rows)
        if combined_row is None:
            return (
                False,
                "The table is missing a combined price row. Add a row within the same table whose 'Product' cell indicates a total "
                "(e.g., 'Total', 'Combined', or 'Grand Total') and whose 'Price (USD)' cell contains the computed combined amount."
            )

        # If we reach here, this table passes the checks
        return (
            True,
            "Format is valid: found a Markdown table with headers 'Product' and 'Price (USD)' and a combined price row containing a USD value."
        )

    # Fallback (should not be reached due to returns inside loop)
    return (
        False,
        "A Markdown table was found but it did not meet the required structure. Ensure exactly two headers "
        "('Product', 'Price (USD)') and include a combined price row with a numeric USD value."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the response ends with a period '.' after trimming trailing whitespace.
    """
    trimmed = response.rstrip()
    if not trimmed:
        return (
            False,
            "The response is empty. Provide a response that ends with a period '.'."
        )
    if not trimmed.endswith("."):
        return (
            False,
            "The response must end with a period '.'. Add a period to the very end of the response (after any tables or text)."
        )
    return (
        True,
        "Punctuation is valid: the response ends with a period."
    )

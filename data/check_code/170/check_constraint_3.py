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
 The agent must invoke between 1 and 4 unique tool types simultaneously in any single interaction turn. The minimum of 1 must be achieved in at least one turn, and the maximum of 4 must not be exceeded in any turn. The total number of interaction turns must fall within a range of 8 to 10. The agent is allowed to invoke the advanced_calculator function at most 1 time during the solution process. The response must include the keywords "Step X:" for each major action or reasoning step, where X is a sequential number, to clearly delineate the logical progression of the solution. The final answer must be concise and not exceed 100 characters and must end with a period to ensure proper sentence closure. Additionally, the final answer must contain a table that clearly shows the calculated difference between the flight distance and the train distance, with appropriate column headers and aligned data. The table must include the two distances and the difference as distinct rows or columns for clarity. Furthermore, the `river_origin_locator` must be invoked before the `explorer_identifier`, and the `cultural_landmark_identifier` must be invoked before the `financial_hub_identifier`.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', 'The response must include the keywords "Step X:" for each major action or reasoning step, where X is a sequential number, to clearly delineate the logical progression of the solution.')
- idx 3: ('Response', 'Punctuation', 'The final answer must end with a period to ensure proper sentence closure.')
- idx 4: ('Response', 'Format', 'The final answer must contain a table that clearly shows the calculated difference between the flight distance and the train distance, with appropriate column headers and aligned data. The table must include the two distances and the difference as distinct rows or columns for clarity.')
"""

import re
from typing import Tuple, List, Optional


# -------------------------
# Helper functions
# -------------------------

SECTION_HEADER_PATTERN = re.compile(r'(?im)^\[[A-Z][A-Z ]+\]\s*')


def extract_section(text: str, header: str = "FINAL ANSWER") -> Optional[str]:
    """
    Extract the content of a section like [FINAL ANSWER] ... until the next [ALL CAPS] header or end of text.
    Returns None if the section header is not present.
    """
    pattern = re.compile(r'(?im)^\[' + re.escape(header) + r'\]\s*')
    m = pattern.search(text)
    if not m:
        return None
    start = m.end()
    m2 = SECTION_HEADER_PATTERN.search(text, start)
    end = m2.start() if m2 else len(text)
    return text[start:end].strip()


def _is_pipe_separator_row(line: str) -> bool:
    """Detects markdown pipe-table separator rows like |---|:---:|---|."""
    stripped = line.strip().strip('|').strip()
    if not stripped:
        return False
    return all(ch in "-: " for ch in stripped)


def _split_pipe_row(line: str) -> List[str]:
    # Split by '|' and strip cells; drop leading/trailing empty cells from edges
    parts = [c.strip() for c in line.split('|')]
    # Remove leading/trailing empty if line starts/ends with pipe
    if parts and parts[0] == '':
        parts = parts[1:]
    if parts and parts[-1] == '':
        parts = parts[:-1]
    return parts


def parse_pipe_tables(text: str) -> List[List[List[str]]]:
    """
    Parse consecutive lines with '|' into candidate pipe tables.
    Returns a list of tables; each table is a list of rows; each row is a list of cells (strings).
    """
    lines = text.splitlines()
    blocks: List[List[str]] = []
    curr: List[str] = []
    for line in lines:
        if line.count('|') >= 2:
            curr.append(line)
        else:
            if len(curr) >= 2:
                blocks.append(curr)
            curr = []
    if len(curr) >= 2:
        blocks.append(curr)

    tables: List[List[List[str]]] = []
    for block in blocks:
        rows = []
        for line in block:
            if _is_pipe_separator_row(line):
                # keep as a separator marker by storing a special token row; we will skip in validation
                rows.append(["__SEP__"])
            else:
                rows.append(_split_pipe_row(line))
        # Ensure there are at least two data rows (ignoring separator rows)
        data_rows = [r for r in rows if r != ["__SEP__"]]
        if len(data_rows) >= 2:
            # Check column consistency across data rows
            col_counts = {len(r) for r in data_rows}
            if len(col_counts) == 1:
                tables.append(rows)
    return tables


SPACE_ROW_REGEX = re.compile(r'\S(?:\s{2,}\S)+')


def parse_space_tables(text: str) -> List[List[List[str]]]:
    """
    Parse text blocks where rows contain columns separated by at least two spaces.
    Returns a list of tables; each table is a list of rows; each row is a list of cells.
    """
    lines = text.splitlines()
    blocks: List[List[str]] = []
    curr: List[str] = []

    def is_space_row(line: str) -> bool:
        return bool(SPACE_ROW_REGEX.search(line.strip()))

    for line in lines:
        if is_space_row(line):
            curr.append(line)
        else:
            if len(curr) >= 2:
                blocks.append(curr)
            curr = []
    if len(curr) >= 2:
        blocks.append(curr)

    tables: List[List[List[str]]] = []
    for block in blocks:
        rows = [re.split(r'\s{2,}', ln.strip()) for ln in block]
        # Filter empty rows or rows with only 1 col
        rows = [r for r in rows if len(r) >= 2]
        if len(rows) >= 2:
            col_counts = {len(r) for r in rows}
            if len(col_counts) == 1:
                tables.append(rows)
    return tables


def _contains_number(s: str) -> bool:
    return bool(re.search(r'\d', s))


def _has_required_labels_in_table_rows(rows: List[List[str]]) -> bool:
    """
    Check whether a table (rows of cells) contains the required labels:
    'flight', 'train', and 'difference', either:
      - as column headers (in the first non-separator row), or
      - as distinct row labels in the first column.
    """
    # Remove separator rows used in pipe tables
    clean_rows = [r for r in rows if r != ["__SEP__"]]
    if not clean_rows:
        return False

    # Header-based detection
    header = [c.lower() for c in clean_rows[0]]
    header_text = " | ".join(header)
    has_header_terms = all(term in header_text for term in (
        "flight", "train", "difference"))

    if has_header_terms:
        return True

    # Row-label-based detection (first column)
    first_col = [r[0].lower()
                 for r in clean_rows if r and isinstance(r[0], str)]
    has_flight_row = any("flight" in c for c in first_col)
    has_train_row = any("train" in c for c in first_col)
    has_difference_row = any(
        "difference" in c or "diff" in c for c in first_col)

    return has_flight_row and has_train_row and has_difference_row


def _table_has_some_numeric_values(rows: List[List[str]]) -> bool:
    """Ensure at least one numeric value appears in the table cells."""
    for r in rows:
        if r == ["__SEP__"]:
            continue
        for c in r:
            if _contains_number(c):
                return True
    return False


# -------------------------
# Validators
# -------------------------

def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes 'Step X:' markers:
      - At least one occurrence
      - Numbers are positive integers
      - Steps are sequential with no gaps starting from 1
      - Steps appear in ascending order
      - Exact token 'Step' (capital S) and a trailing colon ':'
    """
    pattern = re.compile(r'\bStep\s+(\d+)\s*:', flags=re.MULTILINE)
    matches = list(pattern.finditer(response))
    if not matches:
        return (
            False,
            "Missing 'Step X:' markers. Add lines like 'Step 1:', 'Step 2:' etc. "
            "Use capital 'S' in 'Step', include a space before the number, and end with a colon ':'. "
            "Start numbering at 1 and include a marker for each major action or reasoning step."
        )

    numbers = [int(m.group(1)) for m in matches]
    # Check ascending order of occurrences
    if numbers != sorted(numbers):
        return (
            False,
            "The 'Step X:' markers are out of order. Ensure steps appear in ascending order "
            "(e.g., Step 1:, Step 2:, Step 3:) and do not reorder or repeat numbers."
        )

    max_n = max(numbers)
    expected = list(range(1, max_n + 1))
    if numbers != expected:
        # Identify missing or duplicate steps
        observed_set = set(numbers)
        missing = [str(n) for n in expected if n not in observed_set]
        duplicates = [str(n) for n in numbers if numbers.count(n) > 1]
        detail = []
        if missing:
            detail.append(
                f"missing steps: {', '.join(sorted(set(missing), key=int))}")
        if duplicates:
            # show unique duplicates only
            dup_unique = sorted({d for d in duplicates}, key=int)
            detail.append(f"duplicates: {', '.join(dup_unique)}")
        reason = "; ".join(detail) if detail else "non-sequential numbering"
        return (
            False,
            f"'Step X:' markers must be sequential without gaps starting at 1; {reason}. "
            "Add any missing steps, remove duplicates, and keep the exact format 'Step N:' with a colon."
        )

    return (
        True,
        "OK: Found sequential 'Step X:' markers starting at 1 with correct ordering and format."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the [FINAL ANSWER] section ends with a period '.'.
    If the section is missing, check the entire response as a fallback.
    """
    final_answer = extract_section(response, "FINAL ANSWER")
    scope = final_answer if final_answer is not None else response
    scope_name = "[FINAL ANSWER]" if final_answer is not None else "response"

    stripped = scope.rstrip()
    if not stripped:
        return (
            False,
            "No content found to validate punctuation. Provide a concise [FINAL ANSWER] that ends with a period '.'."
        )

    if stripped.endswith("."):
        return (
            True,
            "OK: The final answer ends with a period."
        )

    return (
        False,
        f"The {scope_name} must end with a period '.'. If your last line is a table row, "
        "append a short closing sentence after the table, ending with a period."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the [FINAL ANSWER] contains a table that:
      - Is a recognizable table (Markdown pipe table or space-aligned columns)
      - Contains the concepts 'Flight', 'Train', and 'Difference' as distinct rows or columns
      - Has reasonably aligned/consistent columns across rows
      - Contains at least one numeric value (distance/difference)
    """
    final_answer = extract_section(response, "FINAL ANSWER")
    if final_answer is None:
        return (
            False,
            "Missing [FINAL ANSWER] section. Include a table in [FINAL ANSWER] showing "
            "Flight distance, Train distance, and their Difference as distinct rows or columns."
        )

    pipe_tables = parse_pipe_tables(final_answer)
    space_tables = parse_space_tables(final_answer)

    # Combine all tables into a single list normalized as rows of cells
    candidate_tables: List[List[List[str]]] = []

    # Normalize pipe tables: keep as-is
    for t in pipe_tables:
        candidate_tables.append(t)

    # Normalize space tables: already rows of cells
    for t in space_tables:
        candidate_tables.append(t)

    if not candidate_tables:
        return (
            False,
            "No valid table detected in [FINAL ANSWER]. Use either a Markdown pipe table (with '|' and a header "
            "separator like |---|) or a space-aligned table with at least two rows and consistent columns. "
            "Ensure the table includes Flight, Train, and Difference."
        )

    # Evaluate each table against required labels and presence of numbers
    for rows in candidate_tables:
        has_labels = _has_required_labels_in_table_rows(rows)
        has_numbers = _table_has_some_numeric_values(rows)
        # Check column consistency for alignment in non-separator rows
        data_rows = [r for r in rows if r != ["__SEP__"]]
        col_counts = {len(r) for r in data_rows} if data_rows else set()

        if has_labels and has_numbers and len(col_counts) == 1:
            return (
                True,
                "OK: Found a properly structured table with Flight, Train, and Difference and numeric values."
            )

    # If we reach here, tables were found but did not meet all requirements
    issues = []
    if not any(_has_required_labels_in_table_rows(r) for r in candidate_tables):
        issues.append(
            "missing required labels ('Flight', 'Train', 'Difference')")
    if not any(_table_has_some_numeric_values(r) for r in candidate_tables):
        issues.append("no numeric values present")
    if not any(len({len(row) for row in [rr for rr in r if rr != ['__SEP__']]}) == 1 for r in candidate_tables):
        issues.append("inconsistent column alignment")

    detail = "; ".join(
        issues) if issues else "table did not match required format"

    return (
        False,
        "The table in [FINAL ANSWER] is invalid: " + detail + ". "
        "Fix by ensuring consistent columns and including either: "
        "(A) a header with columns 'Flight', 'Train', 'Difference', or "
        "(B) the first column labels 'Flight', 'Train', 'Difference' on separate rows, "
        "and include numeric values for both distances and the difference. "
        "Example (Markdown):\n"
        "| Metric | Value |\n|---|---|\n| Flight | 500 km |\n| Train | 450 km |\n| Difference | 50 km |"
    )

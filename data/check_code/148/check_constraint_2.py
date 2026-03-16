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
 If the agent intends to use the `historical_event_date_tool`, it must be invoked in a single action step to retrieve the necessary dates. At least one interaction turn must involve the agent invoking at least one unique tool type simultaneously. All information must be obtained through tool calls, and the agent must analyze and correct any errors until it arrives at a final answer. The total number of interaction turns must fall within a range of 2 to 5 (inclusive). The final answer must contain a table with at least two rows and two columns to clearly show the event names, their respective dates, and the calculated number of days between them. Additionally, the response must conclude with the phrase "Days between events: [number]" and must be between 150 and 250 words in total length to ensure conciseness and completeness.

response_constraints_non_length:
- idx 2: ('Response', 'Format', '(Response, Table, Must contain a table with at least two rows and two columns to clearly show the event names, their respective dates, and the calculated number of days between them.)')
- idx 3: ('Response', 'Identifiers', 'Must conclude with the phrase "Days between events: [number]"')
"""

import re
from typing import List, Tuple, Dict


# --------- Helpers for table detection and analysis ---------

def _split_markdown_row(row: str) -> List[str]:
    # Remove leading/trailing pipe and split
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [col.strip() for col in row.split("|")]


def _is_markdown_sep(row: str) -> bool:
    # Typical Markdown separator line: |---|:---:|---|
    row = row.strip()
    if not row:
        return False
    # Accept both with and without leading/trailing pipe
    pattern = r'^\|?\s*(:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$'
    return re.match(pattern, row) is not None


def _find_markdown_tables(lines: List[str]) -> List[Dict]:
    tables = []
    i = 0
    n = len(lines)
    while i < n - 1:
        header_candidate = lines[i].strip()
        if header_candidate.startswith("|") and "|" in header_candidate:
            if _is_markdown_sep(lines[i + 1]):
                headers = _split_markdown_row(header_candidate)
                rows = []
                j = i + 2
                while j < n:
                    line = lines[j].strip()
                    if line.startswith("|") and "|" in line and not _is_markdown_sep(line):
                        rows.append(_split_markdown_row(line))
                        j += 1
                    else:
                        break
                tables.append({
                    "type": "markdown",
                    "headers": headers,
                    "rows": rows
                })
                i = j
                continue
        i += 1
    return tables


def _split_csv_row(row: str) -> List[str]:
    # Simple CSV split (no quoted commas handling)
    return [col.strip() for col in row.split(",")]


def _find_csv_tables(lines: List[str]) -> List[Dict]:
    tables = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if "," in line:
            headers = _split_csv_row(line)
            rows = []
            j = i + 1
            # Collect subsequent lines with same column count
            while j < n and "," in lines[j]:
                cols = _split_csv_row(lines[j].strip())
                # Require consistent column count to consider a table
                if len(cols) == len(headers):
                    rows.append(cols)
                    j += 1
                else:
                    break
            # Consider it a table if we have at least 2 data rows
            if len(rows) >= 2:
                tables.append({
                    "type": "csv",
                    "headers": headers,
                    "rows": rows
                })
                i = j
                continue
        i += 1
    return tables


def _normalize_header_tokens(headers: List[str]) -> List[str]:
    return [re.sub(r'\s+', ' ', h).strip().lower() for h in headers]


def _has_required_columns(headers: List[str]) -> Dict[str, bool]:
    tokens = _normalize_header_tokens(headers)
    has_event = any(re.search(r'\bevent\b', t) for t in tokens)
    has_date = any(re.search(r'\bdate\b', t) for t in tokens)
    # Days/difference column
    has_days = any(
        re.search(r'\bdays\b', t) or re.search(
            r'\bdifference\b', t) or re.search(r'\bdelta\b', t)
        for t in tokens
    )
    return {"event": has_event, "date": has_date, "days": has_days}


def _contains_days_value(rows: List[List[str]]) -> bool:
    # Look for a numeric cell that is plausibly "days" (integer, optionally with commas)
    num_pattern = re.compile(r'^\d{1,3}(?:,\d{3})*$|^\d+$')
    for row in rows:
        for cell in row:
            cell_clean = cell.strip()
            # Prefer cells that mention "day(s)" near a number, else accept bare integer cells
            if re.search(r'\bdays?\b', cell_clean.lower()) and re.search(r'\d', cell_clean):
                return True
            if num_pattern.match(cell_clean):
                return True
    return False


def _evaluate_tables(tables: List[Dict]) -> Tuple[bool, str]:
    if not tables:
        return False, ("No recognizable table found. Provide a clear table (Markdown preferred) "
                       "with at least two data rows and two columns. Include columns for Event, Date, "
                       "and Days between events.")
    # Check each table for requirements
    for t in tables:
        headers = t.get("headers", [])
        rows = t.get("rows", [])
        col_count = len(headers)
        row_count = len(rows)
        cols_ok = col_count >= 2
        rows_ok = row_count >= 2
        req = _has_required_columns(headers)
        days_value_ok = _contains_days_value(rows) if req["days"] else False

        if cols_ok and rows_ok and req["event"] and req["date"] and req["days"] and days_value_ok:
            return True, ("Valid: The response contains a table with >=2 rows and >=2 columns, "
                          "including Event, Date, and Days between events, with numeric days values.")

    # If none fully valid, construct a detailed guidance message using the best candidate
    best = max(
        tables,
        key=lambda t: (len(t.get("rows", [])) >= 2) + (len(t.get("headers", [])) >= 2) +
        sum(_has_required_columns(t.get("headers", [])).values())
        if t else 0
    )
    headers = best.get("headers", [])
    rows = best.get("rows", [])
    issues = []
    if len(headers) < 2:
        issues.append("Your table has fewer than two columns.")
    if len(rows) < 2:
        issues.append("Your table has fewer than two data rows.")
    req = _has_required_columns(headers)
    if not req["event"]:
        issues.append("Missing an 'Event' column header.")
    if not req["date"]:
        issues.append("Missing a 'Date' column header.")
    if not req["days"]:
        issues.append(
            "Missing a 'Days' or 'Days between events' column header.")
    else:
        if not _contains_days_value(rows):
            issues.append(
                "The 'Days' column lacks a clear numeric value for the days difference.")

    guidance = (
        "Revise your final answer to include a Markdown table like:\n"
        "Event | Date | Days between events\n"
        "--- | --- | ---\n"
        "Event A | YYYY-MM-DD | <days>\n"
        "Event B | YYYY-MM-DD | <days>\n"
        "Ensure at least two data rows and that the 'Days between events' values are numeric."
    )
    return False, " ; ".join(issues) + " " + guidance


# --------- Validators for the specific response constraints ---------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a table with at least two rows and two columns
    that clearly shows event names, their respective dates, and the calculated number
    of days between them.
    """
    lines = response.splitlines()
    md_tables = _find_markdown_tables(lines)
    csv_tables = _find_csv_tables(lines)
    tables = md_tables + csv_tables
    ok, msg = _evaluate_tables(tables)
    return ok, msg


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the exact phrase:
    'Days between events: [number]'
    where [number] is an integer (digits, optional thousands separators).
    """
    # Allow trailing whitespace after the phrase, but no other characters.
    end_pattern = re.compile(
        r'(Days between events:\s*\d{1,3}(?:,\d{3})*|\s*Days between events:\s*\d+)\s*$')
    if end_pattern.search(response) is None:
        # Check if the phrase exists but not at the end, to provide more targeted feedback
        anywhere_pattern = re.compile(r'Days between events:\s*\S+')
        if anywhere_pattern.search(response):
            return (
                False,
                "Place the exact phrase 'Days between events: <number>' at the very end of the response. "
                "Use digits for the number (e.g., 'Days between events: 123'). Remove any trailing punctuation "
                "after the number and avoid additional text following the phrase."
            )
        else:
            return (
                False,
                "Conclude your response with the exact phrase 'Days between events: <number>'. "
                "Replace <number> with an integer (digits only, thousands separators optional), e.g., "
                "'Days between events: 1,234'. Do not add any text or punctuation after this phrase."
            )
    return True, (
        "Valid: The response ends with the required identifier phrase "
        "'Days between events: <number>' and uses a numeric value."
    )

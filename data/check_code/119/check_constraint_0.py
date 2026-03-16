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
 The answer must end with a period to ensure proper sentence closure and must not contain any exclamation marks or question marks to maintain a formal tone. Additionally, if the agent intends to retrieve the required information, it must include at least one interaction turn where two different tool types are invoked simultaneously. The agent must execute a minimum of three distinct tool calls across all interaction turns to thoroughly investigate the price data. The answer must be at most 200 characters in length to ensure conciseness. Finally, the answer must contain a table with headers for 'Date' and 'Price', and two rows for today and tomorrow's prices to clearly present the comparison.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The answer must end with a period to ensure proper sentence closure and must not contain any exclamation marks or question marks to maintain a formal tone.')
- idx 5: ('Response', 'Format', "(Response, Table, The answer must contain a table with headers for 'Date' and 'Price', and two rows for today and tomorrow's prices)")
"""

import re
from typing import Tuple, List, Optional
from datetime import date, timedelta, datetime

# ---------------------------
# Helper utilities
# ---------------------------


def _strip_pipes(line: str) -> str:
    return re.sub(r'^\s*\|\s*', '', re.sub(r'\s*\|\s*$', '', line)).strip()


def _split_markdown_row(line: str) -> List[str]:
    line = _strip_pipes(line)
    return [c.strip() for c in line.split('|')]


def _looks_like_md_separator(line: str) -> bool:
    line = line.strip()
    if '|' not in line:
        return False
    core = re.sub(r'[|\s]', '', line)
    return bool(core) and all(ch in '-:' for ch in core)


def _parse_markdown_tables(text: str) -> List[dict]:
    lines = text.splitlines()
    tables = []
    i = 0
    n = len(lines)
    while i < n - 1:
        line = lines[i]
        next_line = lines[i + 1]
        if '|' in line and '|' in next_line and _looks_like_md_separator(next_line):
            headers = _split_markdown_row(line)
            rows = []
            j = i + 2
            while j < n and '|' in lines[j] and not lines[j].strip().startswith('```'):
                row_cells = _split_markdown_row(lines[j])
                if any(cell.strip() for cell in row_cells):
                    rows.append(row_cells)
                j += 1
            tables.append({'headers': headers, 'rows': rows})
            i = j
        else:
            i += 1
    return tables


def _parse_csv_tables(text: str) -> List[dict]:
    lines = [ln for ln in text.splitlines()]
    i = 0
    n = len(lines)
    tables = []
    while i < n:
        if ',' in lines[i]:
            header_cells = [c.strip() for c in lines[i].split(',')]
            rows = []
            j = i + 1
            while j < n and ',' in lines[j]:
                row_cells = [c.strip() for c in lines[j].split(',')]
                if len(row_cells) == len(header_cells):
                    rows.append(row_cells)
                    j += 1
                else:
                    break
            if rows:
                tables.append({'headers': header_cells, 'rows': rows})
                i = j
            else:
                i += 1
        else:
            i += 1
    return tables


def _find_valid_table(tables: List[dict]) -> Optional[dict]:
    for tbl in tables:
        headers_lower = [h.strip().lower() for h in tbl['headers']]
        if 'date' in headers_lower and 'price' in headers_lower:
            date_idx = headers_lower.index('date')
            price_idx = headers_lower.index('price')
            normalized_rows = []
            for r in tbl['rows']:
                if len(r) > max(date_idx, price_idx):
                    normalized_rows.append(r)
            if normalized_rows:
                return {
                    'headers': tbl['headers'],
                    'rows': normalized_rows,
                    'date_idx': date_idx,
                    'price_idx': price_idx
                }
    return None


def _is_today_token(s: str) -> bool:
    return s.strip().lower() == "today"


def _is_tomorrow_token(s: str) -> bool:
    return s.strip().lower() == "tomorrow"


def _parse_date_literal(s: str) -> Optional[date]:
    s_clean = s.strip()
    fmts = [
        '%Y-%m-%d', '%Y/%m/%d',
        '%d-%m-%Y', '%d/%m/%Y',
        '%m-%d-%Y', '%m/%d/%Y'
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s_clean, fmt).date()
        except ValueError:
            continue
    return None


def _is_numeric_price(s: str) -> bool:
    s_clean = s.strip()
    s_clean = re.sub(r'^[^\d\-+]*', '', s_clean)
    s_clean = s_clean.replace(',', '')
    try:
        float(s_clean)
        return True
    except ValueError:
        return False

# ---------------------------
# Constraint validators
# ---------------------------


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Checks:
    - The final answer must end with a period '.'
    - The final answer must not contain '!' or '?'
    """
    text = response.rstrip()
    issues = []
    if '!' in text:
        issues.append(
            "Remove all exclamation marks '!' from the final answer.")
    if '?' in text:
        issues.append("Remove all question marks '?' from the final answer.")
    if not text.endswith('.'):
        issues.append(
            "Ensure the final character of the response is a period '.'. "
            "If the table is last, append a period on a new line after it."
        )
    if issues:
        return False, "Punctuation violations detected: " + " ".join(issues)
    return True, "Punctuation is valid: no '!' or '?' present and the response ends with a period."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Checks that the response contains a table with:
    - Headers including 'Date' and 'Price' (case-insensitive)
    - Exactly two data rows
    - Date rule:
        * Accept 'Today' + 'Tomorrow' (order agnostic), OR
        * Accept two literal dates that differ by exactly 1 day (order agnostic)
        * Do not mix placeholders with literal dates
    - Price values are numeric
    """
    md_tables = _parse_markdown_tables(response)
    csv_tables = _parse_csv_tables(response)
    all_tables = md_tables + csv_tables

    if not all_tables:
        return False, (
            "No table detected. Add a table with headers 'Date' and 'Price' and exactly two rows.\n"
            "Example Markdown:\n| Date | Price |\n|---|---|\n| Today | 0 |\n| Tomorrow | 0 |"
        )

    valid_tbl = _find_valid_table(all_tables)
    if not valid_tbl:
        return False, (
            "A table was found but it does not include headers 'Date' and 'Price'. "
            "Include these headers (any case is fine)."
        )

    rows = [r for r in valid_tbl['rows'] if any(cell.strip() for cell in r)]
    date_idx = valid_tbl['date_idx']
    price_idx = valid_tbl['price_idx']

    if len(rows) != 2:
        return False, (
            f"The table must have exactly two data rows, found {len(rows)}. "
            "Keep only two rows."
        )

    d1 = rows[0][date_idx]
    d2 = rows[1][date_idx]

    # Case 1: Today/Tomorrow tokens (order agnostic)
    if (_is_today_token(d1) and _is_tomorrow_token(d2)) or (_is_today_token(d2) and _is_tomorrow_token(d1)):
        pass
    else:
        # Disallow mixing placeholder with literal date
        token1 = _is_today_token(d1) or _is_tomorrow_token(d1)
        token2 = _is_today_token(d2) or _is_tomorrow_token(d2)
        if token1 or token2:
            return False, (
                "Do not mix 'Today/Tomorrow' with literal dates. "
                "Use either both placeholders or both literal dates."
            )

        p1 = _parse_date_literal(d1)
        p2 = _parse_date_literal(d2)
        if p1 is None or p2 is None:
            return False, (
                f"Invalid Date values '{d1}' and/or '{d2}'. "
                "Use 'Today'/'Tomorrow' or literal dates like YYYY-MM-DD."
            )
        if abs((p1 - p2).days) != 1:
            return False, (
                "The Date column must contain two consecutive days (difference of 1 day). "
                "Use two adjacent dates or 'Today' and 'Tomorrow'."
            )

    # Price validation
    for i, r in enumerate(rows, start=1):
        pcell = r[price_idx]
        if not _is_numeric_price(pcell):
            return False, (
                f"Row {i} has a non-numeric Price value '{pcell}'. "
                "Provide numeric prices (currency symbols allowed)."
            )

    return True, (
        "Format is valid: table contains headers 'Date' and 'Price' with exactly two rows, "
        "valid consecutive dates, and numeric prices."
    )

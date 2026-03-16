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
 The agent's final response must begin with the phrase "The answer is (a)" or "The answer is (b)", depending on which value is higher. The agent must use between 6 to 10 tool calls to gather the necessary information and make its determination. The `scientific_discovery_finder` tool must be invoked before the `historical_site_locator` tool, and the `bestselling_book_author_finder` tool must be invoked before the `residence_finder` tool. Additionally, the `enhanced_nearby_national_park_locator` tool must be invoked before the `biodiversity_info_tool`. Furthermore, the agent must invoke at least one pair of the following tools in parallel within a single action step: `scientific_discovery_finder` and `bestselling_book_author_finder`, or `historical_site_locator` and `residence_finder`, or `enhanced_nearby_national_park_locator` and `nearby_mountain_locator`. The agent's final response must end with a period (.) to ensure proper sentence closure, and must contain a table with two columns: one for the value being compared (species count or mountain height) and one for the corresponding value. The table should have a header row and be formatted using standard table syntax.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Main Category, Start identifier, The agent\'s final response must begin with the phrase "The answer is (a)" or "The answer is (b)", depending on which value is higher.)')
- idx 4: ('Response', 'Punctuation', "The agent's final response must end with a period (.) to ensure proper sentence closure.")
- idx 5: ('Response', 'Format', "(Response, Format, The agent's final response must contain a table, using rows and columns to clearly present data. The table must include two columns: one for the value being compared (species count or mountain height) and one for the corresponding value. The table should have a header row and be formatted using standard table syntax.)")
"""

import re
from typing import List, Tuple, Optional

# -----------------------------
# Helpers: strip final period for parsing only
# -----------------------------


def _strip_final_period_for_table(text: str) -> str:
    """
    Only for table parsing:
    If the last non-whitespace char is '.', remove that dot (keep trailing whitespace).
    """
    if text is None:
        return ""

    # Separate trailing whitespace
    m = re.search(r"\s*\Z", text)
    ws = m.group(0) if m else ""
    core = text[:len(text) - len(ws)] if ws else text

    if core.endswith("."):
        core = core[:-1]

    return core + ws


# -----------------------------
# Helpers to parse Markdown table
# -----------------------------

def _split_table_row(line: str) -> List[str]:
    s = line.strip()
    if '|' not in s:
        return []
    parts = [c.strip() for c in s.split('|')]
    if parts and parts[0] == '':
        parts = parts[1:]
    if parts and parts[-1] == '':
        parts = parts[:-1]
    return parts


def _is_delimiter_row(line: str, min_cols: int = 2) -> bool:
    cells = _split_table_row(line)
    if len(cells) < min_cols:
        return False
    for cell in cells:
        if not re.fullmatch(r':?-{3,}:?', cell.strip()):
            return False
    return True


def _find_first_markdown_table(text: str) -> Optional[Tuple[List[str], List[List[str]]]]:
    # ✅ 用“解析专用”的去句号版本
    prepared = _strip_final_period_for_table(text)

    lines = prepared.splitlines()
    i = 0
    while i < len(lines) - 1:
        header_cells = _split_table_row(lines[i])
        if len(header_cells) >= 2 and _is_delimiter_row(lines[i + 1], min_cols=len(header_cells)):
            data_rows: List[List[str]] = []
            j = i + 2
            while j < len(lines):
                row_cells = _split_table_row(lines[j])
                if len(row_cells) == 0:
                    break
                data_rows.append(row_cells)
                j += 1
            return (header_cells, data_rows)
        i += 1
    return None


def _extract_first_number(s: str) -> Optional[float]:
    m = re.search(r'[-+]?(?:(?:\d{1,3}(?:,\d{3})+)|\d+)(?:\.\d+)?', s)
    if not m:
        return None
    num_str = m.group(0).replace(',', '')
    try:
        return float(num_str)
    except ValueError:
        return None


def _get_first_two_numeric_values_from_first_table(response: str) -> Tuple[Optional[float], Optional[float], str]:
    # ✅ 同样用解析专用版本（避免 “| 4345 |.” 造成多列）
    prepared = _strip_final_period_for_table(response)

    table = _find_first_markdown_table(prepared)
    if table is None:
        return None, None, "No Markdown table found. Include a standard Markdown table with a header row and a delimiter row."

    header, rows = table
    if len(header) != 2:
        return None, None, f"The table must have exactly two columns. Found {len(header)} in the header."

    if len(rows) < 2:
        return None, None, "The table must contain at least two data rows so that values (a) and (b) can be compared."

    for r_idx, r in enumerate(rows[:2], start=1):
        if len(r) < 2:
            return None, None, f"Data row {r_idx} has fewer than 2 cells. Each row must have exactly two cells."
        if len(r) > 2:
            return None, None, f"Data row {r_idx} has more than 2 cells. The table must have exactly two columns."

    a_val = _extract_first_number(rows[0][1])
    b_val = _extract_first_number(rows[1][1])
    if a_val is None or b_val is None:
        which = []
        if a_val is None:
            which.append("(a)")
        if b_val is None:
            which.append("(b)")
        return None, None, f"Could not parse numeric value(s) for {', '.join(which)} from the second column."

    return a_val, b_val, ""


# -----------------------------
# Validators
# -----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    # ✅ 解析用 prepared，但不改原 response
    table = _find_first_markdown_table(response)
    if table is None:
        return False, "Missing table. Add a Markdown table with a header row and a delimiter row."

    header, rows = table
    if len(header) != 2:
        return False, f"The table must have exactly two columns. Found {len(header)} in the header."

    if len(rows) < 2:
        return False, "The table must contain at least two data rows (for values (a) and (b))."

    for r_idx, r in enumerate(rows[:2], start=1):
        if len(r) != 2:
            return False, f"Data row {r_idx} must have exactly two cells but has {len(r)}."

    a_val = _extract_first_number(rows[0][1])
    b_val = _extract_first_number(rows[1][1])
    if a_val is None or b_val is None:
        return False, "The second column must contain numeric values for the first two rows."

    return True, "Format OK."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    trimmed = (response or "").rstrip()
    if not trimmed.endswith("."):
        return False, "The final response must end with a single period '.'."
    return True, "Punctuation OK."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    m = re.match(r'^\s*The answer is \((a|b)\)', response or "")
    if not m:
        return False, "The response must begin exactly with 'The answer is (a)' or 'The answer is (b)'."

    chosen = m.group(1)
    a_val, b_val, err = _get_first_two_numeric_values_from_first_table(
        response)
    if a_val is None or b_val is None:
        return False, "Cannot verify which option is higher because the numeric values could not be parsed. " + err

    if a_val == b_val:
        return False, f"The two compared values are equal ({a_val} == {b_val})."

    correct = "a" if a_val > b_val else "b"
    if chosen != correct:
        return False, f"Start identifier mismatch: chose ({chosen}) but values imply ({correct}) (a={a_val}, b={b_val})."

    return True, f"Identifiers OK: chose ({chosen}) with a={a_val}, b={b_val}."

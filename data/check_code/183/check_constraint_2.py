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
 The answer must be obtained by invoking the provided tools and must include at least one interaction turn where at least two unique tool types are invoked simultaneously. If the agent decides to invoke `train_speed_analyzer`, it is strictly required to simultaneously invoke `landmark_information_retriever` within the same interaction turn. Additionally, the solution must be derived within a maximum of 10 interaction turns. At least one interaction turn must involve the concurrent invocation of two distinct tools. The answer must be presented in a tabular format with two columns: "Entity" and "Value", separated by a delimiter such as a comma or tab. The final response must not use period.

response_constraints_non_length:
- idx 2: ('Response', 'Format', '(Main Category, Subcategory, The answer must be presented in a tabular format with two columns: one for the entity being compared and one for its corresponding value, separated by a delimiter such as a comma or tab.)')
- idx 3: ('Response', 'Identifiers', '(Response, Delimiting identifier, The answer must be presented in a tabular format with two columns: "Entity" and "Value".)')
- idx 4: ('Response', 'Punctuation', 'The answer must not use period.')
"""

import re
from typing import List, Tuple, Optional

# Helper functions


def _non_empty_lines(text: str) -> List[str]:
    """Return a list of non-empty lines preserving original order."""
    return [ln for ln in text.splitlines() if ln.strip() != ""]


def _detect_delimiter_from_header(header: str) -> Optional[str]:
    """
    Detect delimiter from the header line.
    Returns '\t' for tab, ',' for comma, or None if not detectable.
    Preference is:
      - If header contains a tab and split into exactly 2 parts -> tab
      - Else if header contains a comma and split into exactly 2 parts -> comma
    """
    if "\t" in header:
        parts = header.split("\t")
        if len(parts) == 2:
            return "\t"
    if "," in header:
        parts = header.split(",")
        if len(parts) == 2:
            return ","
    return None


def _validate_two_columns(lines: List[str], delim: str) -> Tuple[bool, str]:
    """
    Ensure every non-empty line contains exactly two columns when split by the delimiter.
    Returns (ok, detail_message).
    """
    for idx, line in enumerate(lines, start=1):
        if delim not in line:
            delimiter_name = "TAB" if delim == "\t" else ","
            return (
                False,
                f"Line {idx} does not contain the required delimiter. "
                f"Expected a single '{delimiter_name}' between two columns."
            )
        parts = line.split(delim)
        if len(parts) != 2:
            # Provide a hint if there are multiple commas/tabs
            count = len(parts) - 1
            return (
                False,
                f"Line {idx} splits into {len(parts)} columns using the chosen delimiter (count of delimiters: {count}). "
                "Each row must have exactly two columns: one entity and one value. "
                "Remove extra delimiters or merge content so only one delimiter appears per row."
            )
        left, right = parts[0].strip(), parts[1].strip()
        if left == "" or right == "":
            return (
                False,
                f"Line {idx} has an empty {'Entity' if left == '' else 'Value'} cell. "
                "Both columns must be non-empty after trimming whitespace."
            )
    return True, "All lines have exactly two non-empty columns using a consistent delimiter."


def _summarize_bad_char_context(text: str, char: str, max_hits: int = 5, context: int = 12) -> str:
    """Return a compact summary of up to max_hits occurrences of char with surrounding context."""
    hits = [m.start() for m in re.finditer(re.escape(char), text)]
    snippets = []
    for i, pos in enumerate(hits[:max_hits], start=1):
        start = max(0, pos - context)
        end = min(len(text), pos + context + 1)
        snippet = text[start:end].replace("\n", "\\n")
        snippets.append(f"{i}) ...{snippet}...")
    more = "" if len(hits) <= max_hits else f" (+{len(hits)-max_hits} more)"
    return "; ".join(snippets) + more if snippets else ""


# Validators

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is a two-column table separated consistently by either a comma or a tab.
    Requirements:
      - The first non-empty line must be the table header.
      - A valid delimiter (comma or tab) is used consistently across all lines.
      - Each non-empty line must split into exactly two non-empty columns.
      - There must be at least one data row after the header.
      - No extra commentary outside of the table (i.e., every non-empty line must be a two-column row).
    """
    lines = _non_empty_lines(response)
    if not lines:
        return False, "The response is empty. Provide a two-column table with a header and at least one data row."

    header = lines[0]
    delim = _detect_delimiter_from_header(header)
    if delim is None:
        return (
            False,
            "The first non-empty line must be the header using a valid delimiter. "
            "Expected exactly 'Entity,Value' or 'Entity<TAB>Value'. "
            "Use either a single comma or a single tab between the two header cells."
        )

    # Verify each line is a two-column row using the detected delimiter
    ok, msg = _validate_two_columns(lines, delim)
    if not ok:
        return False, msg

    # Require at least one data row after the header
    if len(lines) < 2:
        return (
            False,
            "The table has only the header row. Add at least one data row with exactly two columns separated by the same delimiter."
        )

    delimiter_name = "tab" if delim == "\t" else "comma"
    return True, (
        "Format is valid: a consistent two-column table detected using "
        f"{delimiter_name} as the delimiter, with a header and at least one data row."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the header row explicitly uses the identifiers 'Entity' and 'Value' as the two column names.
    Requirements:
      - The first non-empty line must be the header.
      - The header must contain exactly two cells named 'Entity' and 'Value' (case-sensitive) in this order.
      - The header delimiter must be either a comma or a tab.
    """
    lines = _non_empty_lines(response)
    if not lines:
        return False, "The response is empty. The first non-empty line must be the header 'Entity,Value' or 'Entity<TAB>Value'."

    header = lines[0]
    delim = _detect_delimiter_from_header(header)
    if delim is None:
        return (
            False,
            "Header is missing a valid delimiter. Use exactly 'Entity,Value' for comma or 'Entity<TAB>Value' for tab as the first non-empty line."
        )

    parts = [p.strip() for p in header.split(delim)]
    if len(parts) != 2:
        return (
            False,
            "Header must contain exactly two cells. Use 'Entity,Value' or 'Entity<TAB>Value' with no extra delimiters."
        )

    expected_left, expected_right = "Entity", "Value"
    left_ok = parts[0] == expected_left
    right_ok = parts[1] == expected_right

    if not (left_ok and right_ok):
        delimiter_str = "," if delim == "," else "\t"

        return (
            False,
            f"Header identifiers are incorrect. Expected exactly "
            f"'{expected_left}{delimiter_str}{expected_right}'. "
            f"Found '{parts[0]}' and '{parts[1]}'. "
            "Ensure correct casing and ordering: first 'Entity', then 'Value'."
        )

    return True, "Header identifiers are valid: exactly 'Entity' and 'Value' in the correct order."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response does not contain any period characters '.'.
    This includes sentence periods and decimal points. Replace periods with alternatives
    such as 'point' for decimals or remove trailing sentence periods.
    """
    if "." in response:
        context = _summarize_bad_char_context(response, ".")
        return (
            False,
            "The response contains one or more period characters '.'. "
            "Remove all periods, including those used as sentence endings or decimal points. "
            "For numbers, use 'point' or another non-period separator (e.g., '3 point 14'). "
            f"Example locations: {context}".strip()
        )
    return True, "No periods detected in the response."

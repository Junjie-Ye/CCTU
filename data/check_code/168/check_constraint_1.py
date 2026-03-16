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
 If the agent intends to invoke `specialty_beverage_locator`, the `nearby_plant_locator` must be executed beforehand. Additionally, if the agent chooses to use both `fort_feature_locator` and `nearby_plant_locator`, they must be invoked in the same action step. The agent's response must include the delimiter "##" to separate the page count of the novel from the average number of patients treated per day at the hospital, and the final answer must be presented in a tabular format with the following rows: "Novel Page Count" and "Average Patients Treated Per Day".

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Main Category, Delimiting identifier, The agent\'s response must include the delimiter "##" to separate the page count of the novel from the average number of patients treated per day at the hospital.)')
- idx 2: ('Response', 'Format', '(Response, Format, The agent\'s entire response must be organized in a tabular format, with a row for the page count of the novel and a row for the average number of patients treated per day at the hospital, using the delimiter "##" to separate the values.)')
"""

import re
from typing import Tuple, Dict, Optional

# Constants for required labels and delimiter
REQUIRED_LABELS = ("Novel Page Count", "Average Patients Treated Per Day")
DELIMITER = "##"

# Compiled regex to match a single table row with exactly two columns: label and value.
# The row must start and end with a pipe, and the value must not contain any additional pipes.
ROW_PATTERN = re.compile(
    r'^\s*\|\s*(?P<label>Novel Page Count|Average Patients Treated Per Day)\s*\|\s*(?P<value>[^\|]+?)\s*\|\s*$'
)


def _extract_rows(response: str) -> Tuple[Optional[Dict[str, str]], str, list]:
    """
    Helper: Extract table rows and values from the response.
    Returns (rows_dict_or_None, error_message, non_empty_lines)
    - rows_dict_or_None: dict {label: value} if parsing succeeded for all required labels; else None
    - error_message: detailed English error if parsing fails; empty string if no error
    - non_empty_lines: list of non-empty lines (stripped of trailing newlines)
    """
    lines = [ln.rstrip("\n") for ln in response.splitlines()]
    non_empty_lines = [ln for ln in lines if ln.strip() != ""]
    rows: Dict[str, str] = {}

    # Basic count check
    if len(non_empty_lines) != 2:
        return (
            None,
            "The response must consist of exactly 2 non-empty table rows. "
            "Remove any extra lines or blank content and provide only:\n"
            "- One row for 'Novel Page Count'\n"
            "- One row for 'Average Patients Treated Per Day'\n"
            "Each row must be in the form: '| Label | Value |'.",
            non_empty_lines,
        )

    # Parse each line as a table row
    for ln in non_empty_lines:
        m = ROW_PATTERN.match(ln)
        if not m:
            return (
                None,
                "Each line must be a pipe-delimited table row that starts and ends with '|', "
                "contains exactly two columns (Label and Value), and uses the exact labels:\n"
                "- '| Novel Page Count | <value> |'\n"
                "- '| Average Patients Treated Per Day | <value> |'\n"
                "Ensure there are no extra '|' characters inside the value cell.",
                non_empty_lines,
            )
        label = m.group("label").strip()
        value = m.group("value").strip()
        rows[label] = value

    # Check required labels presence
    for lbl in REQUIRED_LABELS:
        if lbl not in rows:
            return (
                None,
                f"Missing required row with the exact label '{lbl}'. "
                "Provide both required rows using the exact label text.",
                non_empty_lines,
            )

    # Ensure values are non-empty
    for lbl, val in rows.items():
        if val.strip() == "":
            return (
                None,
                f"The value cell for '{lbl}' must be non-empty. "
                "Provide a concrete value in the second column, e.g., '| {lbl} | 123 |'.",
                non_empty_lines,
            )

    return rows, "", non_empty_lines


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the 'format' constraint:
    - The entire response must be organized as a two-row table.
    - Each row must be of the form: '| Label | Value |'.
    - The two labels must be exactly 'Novel Page Count' and 'Average Patients Treated Per Day'.
    - Only two rows and two columns are allowed; no extra narrative or lines.
    Note: The delimiter '##' presence is validated by validate_identifiers; here we focus on structure.
    """
    rows, err, non_empty_lines = _extract_rows(response)
    if rows is None:
        return False, err

    # Ensure the response contains only the two table lines (no extra content)
    if len(non_empty_lines) != 2:
        return (
            False,
            "Your response must contain only the two table rows and nothing else. "
            "Remove any additional text or blank lines.",
        )

    return True, (
        "Format validation passed. The response is a two-row, pipe-delimited table with the correct labels. "
        "Keep the structure exactly as '| Label | Value |' for both rows."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the 'identifiers' constraint for the delimiter '##':
    - The response must include the delimiter '##' exactly once.
    - Place '##' at the end of the value in the 'Novel Page Count' row (e.g., '| Novel Page Count | 345 ## |').
    - The 'Average Patients Treated Per Day' row must NOT contain '##'.
    - '##' must appear inside a value cell, not in labels or outside the table.
    """
    rows, err, _ = _extract_rows(response)
    if rows is None:
        return False, (
            "Identifier validation cannot proceed until the table format is corrected. "
            + err
        )

    delimiter_count = response.count(DELIMITER)
    if delimiter_count == 0:
        return False, (
            "Insert the delimiter '##' exactly once to separate the two values. "
            "Place it at the end of the value in the 'Novel Page Count' row, e.g., "
            "'| Novel Page Count | 345 ## |'. Do not add '##' to the second row."
        )
    if delimiter_count > 1:
        return False, (
            "Use the delimiter '##' exactly once. Remove any extra occurrences. "
            "It must appear only at the end of the value in the 'Novel Page Count' row, e.g., "
            "'| Novel Page Count | 345 ## |'. Ensure the 'Average Patients Treated Per Day' row contains no '##'."
        )

    npc_val = rows["Novel Page Count"]
    apd_val = rows["Average Patients Treated Per Day"]

    # '##' must be present only in the first row's value and at the end (optionally followed by spaces)
    npc_has_delim_at_end = bool(re.search(r'\s*##\s*$', npc_val))
    apd_has_delim = DELIMITER in apd_val

    if not npc_has_delim_at_end:
        return False, (
            "Place the delimiter '##' at the end of the 'Novel Page Count' value. "
            "For example: '| Novel Page Count | 345 ## |'. "
            "Do not place '##' at the beginning, middle, or outside of the value cell."
        )
    if apd_has_delim:
        return False, (
            "The 'Average Patients Treated Per Day' row must not contain '##'. "
            "Remove '##' from that row and ensure it appears only at the end of the first row's value."
        )

    return True, (
        "Identifier validation passed. The delimiter '##' is used exactly once and correctly placed "
        "at the end of the 'Novel Page Count' value."
    )

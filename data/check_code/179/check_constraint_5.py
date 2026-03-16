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
 If the agent invokes multiple tools to obtain the required data for comparison, the agent is permitted to invoke `academic_paper_finder` and `innovation_country_identifier` concurrently. Additionally, each of the tools can be used at most once per task to ensure efficient resource allocation. Furthermore, the agent must perform at least 6 interaction rounds to solve the problem. The 'biodiversity_database' tool must be called before the 'satellite_info_retriever' tool in the sequence of actions. The response must include the phrase "Species Count: " followed by the number of species, and the phrase "Satellite Weight (kg): " followed by the weight of the satellite, separated by a line containing "---- Comparison ----" before the final comparison statement. The final comparison statement must end with a period to ensure proper sentence closure.

response_constraints_non_length:
- idx 3: ('Response', 'Identifiers', '(Response, Delimiting identifier, The response must include the phrase "Species Count: " followed by the number of species, and the phrase "Satellite Weight (kg): " followed by the weight of the satellite, separated by a line containing "---- Comparison ----" before the final comparison statement.)')
- idx 5: ('Response', 'Punctuation', '(Response, Punctuation, "The final comparison statement must end with a period to ensure proper sentence closure.")')
"""

import re
from typing import Tuple, List, Optional

# Helper regex patterns (anchored to full line to avoid trailing text)
_SPECIES_LINE_RE = re.compile(r'^Species Count:\s+([0-9][0-9,]*)\s*$')
_WEIGHT_LINE_RE = re.compile(
    r'^Satellite Weight \(kg\):\s+([0-9][0-9,]*(?:\.[0-9]+)?)\s*$')
_COMPARISON_DELIMITER = '---- Comparison ----'


def _split_lines(response: str) -> List[str]:
    """Split response into lines without dropping empty lines."""
    return response.splitlines()


def _find_delimiter_index(lines: List[str]) -> int:
    """Return index of the delimiter line, or -1 if not found."""
    for i, line in enumerate(lines):
        if line.strip() == _COMPARISON_DELIMITER:
            return i
    return -1


def _find_first_nonempty_after(lines: List[str], start_idx_exclusive: int) -> Optional[int]:
    """Return index of the first non-empty line after start_idx_exclusive, or None if none exists."""
    for i in range(start_idx_exclusive + 1, len(lines)):
        if lines[i].strip():
            return i
    return None


def _find_last_nonempty_after(lines: List[str], start_idx_exclusive: int) -> Optional[int]:
    """Return index of the last non-empty line after start_idx_exclusive, or None if none exists."""
    idx = None
    for i in range(start_idx_exclusive + 1, len(lines)):
        if lines[i].strip():
            idx = i
    return idx


def _find_match_before(pattern: re.Pattern, lines: List[str], end_idx_inclusive: int) -> Optional[re.Match]:
    """Search from start up to end_idx_inclusive for a line that matches the pattern; return the match object or None."""
    limit = max(-1, end_idx_inclusive)
    for i in range(0, limit + 1):
        m = pattern.match(lines[i].rstrip('\n'))
        if m:
            return m
    return None


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes:
    - A line exactly matching 'Species Count: ' followed by an integer number (only digits and optional thousands commas).
    - A line exactly matching 'Satellite Weight (kg): ' followed by a numeric value (digits with optional commas and optional decimal).
    - A delimiter line '---- Comparison ----' that appears after both of the above,
      and there is at least one non-empty comparison statement line after the delimiter.
    """
    lines = _split_lines(response)
    if not lines:
        return (False, "Response is empty. Include the required lines: 'Species Count: <integer>', 'Satellite Weight (kg): <number>', the delimiter line '---- Comparison ----', and a comparison sentence after it.")

    delim_idx = _find_delimiter_index(lines)
    if delim_idx == -1:
        return (False, "Missing delimiter line. Add a standalone line: '---- Comparison ----' between the metric lines and the final comparison statement.")

    # Ensure comparison statement exists after delimiter
    first_stmt_idx = _find_first_nonempty_after(lines, delim_idx)
    if first_stmt_idx is None:
        return (False, "No comparison statement found after the delimiter. After the line '---- Comparison ----', add a non-empty final comparison sentence.")

    # Find species and weight lines BEFORE the delimiter
    species_match = _find_match_before(_SPECIES_LINE_RE, lines, delim_idx - 1)
    weight_match = _find_match_before(_WEIGHT_LINE_RE, lines, delim_idx - 1)

    missing_parts = []
    if species_match is None:
        missing_parts.append(
            "a line exactly like 'Species Count: <integer>' (e.g., 'Species Count: 123')")
    if weight_match is None:
        missing_parts.append(
            "a line exactly like 'Satellite Weight (kg): <number>' (e.g., 'Satellite Weight (kg): 456.7')")

    if missing_parts:
        return (
            False,
            "Missing required identifier lines before the delimiter. Please include "
            + " and ".join(missing_parts)
            + " before the line '---- Comparison ----'. Ensure there is only the numeric value after the colon and no trailing text."
        )

    # If present, provide a positive confirmation including parsed values
    species_val = species_match.group(1) if species_match else "N/A"
    weight_val = weight_match.group(1) if weight_match else "N/A"
    return (
        True,
        f"Identifiers validated. Found 'Species Count: {species_val}' and 'Satellite Weight (kg): {weight_val}' before the delimiter, and a comparison statement after it."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final comparison statement ends with a period '.'.
    If the comparison delimiter exists, the final statement is considered the last non-empty line after the delimiter.
    Otherwise, the validator will look at the last non-empty line of the entire response.
    """
    lines = _split_lines(response)
    if not lines:
        return (False, "Response is empty. Provide a final comparison sentence that ends with a period '.'.")

    delim_idx = _find_delimiter_index(lines)
    # Determine which segment to check: after delimiter if present, else whole response
    if delim_idx != -1:
        stmt_idx = _find_last_nonempty_after(lines, delim_idx)
        if stmt_idx is None:
            return (False, "No comparison sentence found after '---- Comparison ----'. Add a non-empty comparison line after the delimiter that ends with a period '.'.")
        target_line = lines[stmt_idx].rstrip()
    else:
        # Fall back to last non-empty line in the whole response
        target_line = ""
        for line in reversed(lines):
            if line.strip():
                target_line = line.rstrip()
                break
        if not target_line:
            return (False, "No non-empty final line found. Add a final comparison sentence that ends with a period '.'.")

    if not target_line.endswith("."):
        return (
            False,
            "The final comparison statement must end with a period '.'. Add a '.' at the end of the last non-empty comparison line."
        )

    return (True, "Punctuation validated. The final comparison statement ends with a period '.'.")

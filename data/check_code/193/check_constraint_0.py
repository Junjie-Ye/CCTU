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
 The response must include the phrases "Patents: ", "Height: ", and "Distance: " to clearly separate and label the three values being compared.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Response, Delimiting identifier, "The response must include the phrases \'Patents: \', \'Height: \', and \'Distance: \' to clearly separate and label the three values being compared.")')
"""

import re
from typing import Tuple, List, Optional

# Helper constants
LABELS = ["Patents: ", "Height: ", "Distance: "]


def _find_next_label_index(text: str, start: int, labels: List[str]) -> Optional[int]:
    """
    Return the earliest index >= start at which any label in `labels` occurs.
    If none occurs after start, return None.
    """
    positions = []
    for lab in labels:
        idx = text.find(lab, start)
        if idx != -1:
            positions.append(idx)
    if not positions:
        return None
    return min(positions)


def _extract_value_segments_for_label(text: str, label: str, all_labels: List[str]) -> List[str]:
    """
    For each occurrence of `label` in `text`, extract the substring considered as the value:
    - Starts immediately after the label occurrence
    - Ends at the earliest of: next label occurrence (of any label), newline, or end-of-text
    Returns a list of raw value segments (not stripped).
    """
    segments = []
    for m in re.finditer(re.escape(label), text):
        value_start = m.end()
        # Determine the nearest boundary
        next_label_idx = _find_next_label_index(text, value_start, all_labels)
        newline_idx = text.find("\n", value_start)

        candidates = [len(text)]
        if next_label_idx is not None:
            candidates.append(next_label_idx)
        if newline_idx != -1:
            candidates.append(newline_idx)

        value_end = min(candidates)
        segment = text[value_start:value_end]
        segments.append(segment)
    return segments


def _has_meaningful_value(segment: str) -> bool:
    """
    A 'meaningful' value is non-empty after stripping whitespace and common separators,
    and contains at least one alphanumeric character.
    """
    # Trim leading/trailing whitespace
    s = segment.strip()
    if not s:
        return False
    # Remove trivial trailing separators while keeping typical numeric/text content intact
    s = re.sub(r"[\s,;|–—-]+$", "", s).strip()
    if not s:
        return False
    # Require at least one alphanumeric character
    return bool(re.search(r"[A-Za-z0-9]", s))


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the exact phrases
    "Patents: ", "Height: ", and "Distance: " (case-sensitive, including the trailing space)
    and that each is followed by a meaningful, non-empty value before the next label,
    newline, or the end of the response.

    Returns:
      (True, message) if all constraints are satisfied
      (False, detailed_instructions) otherwise
    """
    missing_labels = []
    value_issues = []

    for label in LABELS:
        # Find all occurrences of the exact label (including the trailing space)
        occurrences = list(re.finditer(re.escape(label), response))
        if not occurrences:
            missing_labels.append(label)
            continue

        # Extract value segments for each occurrence and check for at least one valid value
        segments = _extract_value_segments_for_label(response, label, LABELS)
        if not any(_has_meaningful_value(seg) for seg in segments):
            # No occurrence had a meaningful value after the label
            value_issues.append(label)

    if not missing_labels and not value_issues:
        return (
            True,
            "All identifier constraints satisfied: the response contains the exact phrases "
            "'Patents: ', 'Height: ', and 'Distance: ', each followed by a non-empty, meaningful value."
        )

    problems = []
    if missing_labels:
        problems.append(
            "Missing required exact phrases (case-sensitive, including the trailing space): "
            + ", ".join(f"'{lab}'" for lab in missing_labels)
        )
    if value_issues:
        problems.append(
            "These labels are present but are not immediately followed by a meaningful value: "
            + ", ".join(f"'{lab}'" for lab in value_issues)
        )

    instructions = [
        "Use the exact labels with the trailing space: 'Patents: ', 'Height: ', and 'Distance: '.",
        "Place a meaningful value (at least one alphanumeric character) immediately after each label.",
        "Do not leave a label with an empty value or only punctuation before the next label or newline.",
        "You may format them on one line or multiple lines. Examples:",
        "- Single line: Patents: 12; Height: 828 m; Distance: 384,400 km",
        "- Multiple lines:\n  Patents: 12\n  Height: 828 m\n  Distance: 384,400 km"
    ]

    return (
        False,
        "Identifier constraint not satisfied.\n"
        + "\n".join(problems) + "\nFix by following these rules:\n"
        + "\n".join(instructions)
    )

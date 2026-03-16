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
 Ensure that in at least one interaction turn during the entire task, the agent invokes at least two tool calls simultaneously. The final response must end with a period to ensure proper sentence closure and must include a bullet point (•) to separate the magnification ratio of the Leica Noctilux-M 50mm f/0.95 from the magnification ratio of the Nikon NIKKOR Z 58mm f/0.95 S in the final response.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', 'The final response must end with a period to ensure proper sentence closure.)')
- idx 2: ('Response', 'Identifiers', '("Response", "Delimiting identifier", "Must include a bullet point (•) to separate the magnification ratio of the Leica Noctilux-M 50mm f/0.95 from the magnification ratio of the Nikon NIKKOR Z 58mm f/0.95 S in the final response.")')
"""

import re
from typing import List, Tuple


# ----------------------------
# Helper utilities
# ----------------------------

# e.g., 0.08x, 0.19×, 1x
MAG_PATTERN = re.compile(r'\b(?:\d+(?:\.\d+)?)\s*(?:x|X|×)\b')


def _rstrip_whitespace(s: str) -> str:
    """Return the string with trailing whitespace removed."""
    return s.rstrip()


def _find_magnifications(s: str) -> List[re.Match]:
    """Return all regex matches for magnification patterns."""
    return list(MAG_PATTERN.finditer(s))


def _first_bullet_index(s: str) -> int:
    """Return the index of the first bullet point (•), or -1 if not present."""
    return s.find('•')


def _bullet_between_first_two_mags(s: str) -> bool:
    """
    Check whether a bullet (•) appears between the first two magnification tokens.
    Spaces around the bullet are allowed.
    """
    mags = _find_magnifications(s)
    if len(mags) < 2:
        return False
    first, second = mags[0], mags[1]
    inter_segment = s[first.end():second.start()]
    return '•' in inter_segment


# ----------------------------
# Validators for Response constraints
# ----------------------------

def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the final response ends with a period '.' (after trimming trailing whitespace).
    """
    trimmed = _rstrip_whitespace(response)
    if trimmed.endswith('.'):
        return True, "Pass: The response ends with a period as required."
    # Identify the last visible character to provide a precise correction
    last_visible = trimmed[-1] if trimmed else ''
    if last_visible in {'!', '?', ';', ':'}:
        return (
            False,
            "Fail: The final response must end with a period '.'. Replace the trailing "
            f"'{last_visible}' with a '.' so the very last character is a period. Example fix: "
            "“... 0.08x • 0.19x.”"
        )
    else:
        return (
            False,
            "Fail: The final response must end with a period '.'. Add a period at the very end "
            "of the response (after all content, with no trailing spaces). Example fix: "
            "“... 0.08x • 0.19x.”"
        )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response includes a bullet point (•) used to separate the magnification
    ratio of the Leica Noctilux-M 50mm f/0.95 and the magnification ratio of the
    Nikon NIKKOR Z 58mm f/0.95 S.

    Practical checks:
    - A bullet point character (•, U+2022) must be present.
    - At least two magnification-like tokens must appear (e.g., `0.08x`, `0.19×`).
    - The bullet must be between the first two magnification tokens, serving as the separator.

    Note: Lens names may or may not be present; this validator focuses on the structural use of
    the bullet as a separator between two magnification ratios.
    """
    # 1) Bullet presence
    bullet_idx = _first_bullet_index(response)
    if bullet_idx == -1:
        return (
            False,
            "Fail: Missing bullet point. Insert a single bullet point character (•, U+2022) "
            "between the two magnification ratios so it acts as the separator. "
            "Example: “Leica: 0.08x • Nikon: 0.19x.”"
        )

    # 2) Two magnification ratios must exist
    mags = _find_magnifications(response)
    if len(mags) < 2:
        return (
            False,
            "Fail: Found a bullet point but fewer than two magnification ratios. Provide both "
            "magnification values using a recognizable format like '<number>x' or '<number>×'. "
            "Example: “Leica: 0.08x • Nikon: 0.19x.”"
        )

    # 3) Bullet must be the separator between the first two magnification tokens
    if not _bullet_between_first_two_mags(response):
        first, second = mags[0], mags[1]
        return (
            False,
            "Fail: The bullet point (•) is not placed between the first two magnification ratios. "
            "Move the bullet so it separates the Leica magnification (first) from the Nikon "
            "magnification (second). Example: “Leica: "
            f"{response[first.start():first.end()]} • Nikon: {response[second.start():second.end()]}.”"
        )

    # 4) Optional soft guidance about lens labeling (not required, but helpful)
    # We won't fail if lens names are absent; we only provide a success note.
    return (
        True,
        "Pass: A bullet point (•) separates two magnification ratios. If helpful for clarity, "
        "label the sides explicitly (e.g., “Leica: 0.08x • Nikon: 0.19x.”)."
    )

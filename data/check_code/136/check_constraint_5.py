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
 The solution must involve at least 2 interaction steps and at least one interaction turn where the agent invokes at least two tool calls simultaneously. The agent may use no more than 5 total tool calls across all interaction steps. The 'historical_event_tool' can be called at most 2 times and must called twice simultaneously in the same step. The response must be at most 100 characters and must end with a period. Your response must conclude with the phrase "Final Answer: [X days]" where [X] is the calculated number of days.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Main Category, End identifier, The agent\'s response must conclude with the phrase "Final Answer: [X days]" followed immediately by a punctuation where [X] is the calculated number of days.)')
- idx 5: ('Response', 'Punctuation', 'The response must end with a period.')
"""

import re
from typing import Tuple, Optional

# Shared regex: captures the required closing phrase and ensures it is at the very end.
# Group 1 = integer number of days, Group 2 = the punctuation immediately after "days"
_FINAL_ANSWER_RE = re.compile(r'Final Answer:\s*(\d+)\s+days([^\w\s])\s*$')


def _last_non_whitespace_char(s: str) -> Optional[str]:
    """Return the last non-whitespace character in s, or None if none exists."""
    for ch in reversed(s):
        if not ch.isspace():
            return ch
    return None


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the response concludes with the exact phrase:
    'Final Answer: [X days]' followed immediately by a punctuation mark,
    where X is an integer. The phrase must be at the very end of the response.
    """
    m = _FINAL_ANSWER_RE.search(response)
    if m:
        return True, "OK: The response ends with 'Final Answer: X days' immediately followed by punctuation."

    # Collect specific, actionable feedback
    reasons = []

    if "Final Answer:" not in response:
        reasons.append(
            'Missing the required closing marker "Final Answer:". Place it at the end.')

    # Check if there's a number after the marker (regardless of end position)
    if re.search(r'Final Answer:\s*\d+', response) is None:
        reasons.append(
            "Insert an integer X after 'Final Answer:' (e.g., 'Final Answer: 12 days.').")

    # Check for the exact word 'days' following the number
    if re.search(r'Final Answer:\s*\d+\s+days', response, flags=re.IGNORECASE) is None:
        reasons.append(
            "Include the exact word 'days' immediately after the number (e.g., '... 12 days').")

    # Check punctuation immediately after 'days' (no space)
    if re.search(r'Final Answer:\s*\d+\s+days([^\w\s])', response) is None:
        reasons.append(
            "Add a punctuation mark immediately after 'days' with no space (e.g., 'days.').")

    # Ensure the phrase is the final content (no extra text after the punctuation)
    if re.search(r'Final Answer:\s*\d+\s+days[^\w\s]\s*$', response) is None:
        reasons.append(
            "Ensure this phrase is the final content of the response (no text after it).")

    guidance = (
        "Fix by ending your output with the exact template: 'Final Answer: X days.' "
        "where X is an integer. Example: 'Final Answer: 13 days.'"
    )

    detail = " | ".join(
        reasons) if reasons else "The closing phrase does not match the required pattern."
    return False, f"{detail} {guidance}"


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the response ends with a period '.' as the final character.
    No trailing spaces are allowed after the final period.
    """
    if response.endswith('.'):
        return True, "OK: The response ends with a period."

    # If the last non-whitespace character is a period, trailing spaces must be removed
    if response.rstrip().endswith('.'):
        return False, (
            "Remove trailing whitespace after the final period; the period must be the last character. "
            "Example: end with '... Final Answer: X days.'"
        )

    last = _last_non_whitespace_char(response)
    if last is None:
        return False, (
            "The response is empty. Add content and ensure it ends with a single period, "
            "e.g., 'Final Answer: X days.'"
        )

    return False, (
        f"The response must end with a period. Replace the last character '{last}' with '.' "
        "so the final characters look like '... Final Answer: X days.' with no trailing spaces."
    )

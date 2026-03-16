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
 You must solve this question by interacting with the provided tools, ensuring that the total number of interaction turns falls within a range of 8 to 13 (inclusive), and that the total number of tool calls executed by the agent is within the range of 7 to 12. Your final response must include the identifiers [Chain of Relationships] and [Final Answer] to separate the explanation of the reasoning from the final answer.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '"The agent\'s response must include the identifiers [Chain of Relationships] and [Final Answer] to separate the explanation of the reasoning from the final answer."')
"""

import re
from typing import Tuple

# Helper functions


def _has_alphanumeric(text: str) -> bool:
    """Return True if text contains at least one alphanumeric character."""
    return bool(re.search(r'[A-Za-z0-9]', text))


def _count_occurrences(haystack: str, needle: str) -> int:
    """Count non-overlapping occurrences of needle in haystack (case-sensitive)."""
    return haystack.count(needle)


def _exists_case_insensitive(haystack: str, needle: str) -> bool:
    """Check if needle exists in haystack ignoring case."""
    return re.search(re.escape(needle), haystack, flags=re.IGNORECASE) is not None


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the agent's response includes the identifiers
    '[Chain of Relationships]' and '[Final Answer]' to separate
    the explanation of the reasoning from the final answer.

    Requirements enforced:
    - Both identifiers must be present with exact casing and bracket format.
    - Each identifier must appear exactly once.
    - [Chain of Relationships] must appear before [Final Answer].
    - Content between [Chain of Relationships] and [Final Answer] must be non-empty (contains alphanumeric).
    - Content after [Final Answer] must be non-empty (contains alphanumeric).

    Returns:
        (bool, str): A tuple where bool indicates pass/fail, and str provides
        a detailed, English instruction for fixing issues if any.
    """
    chain_tag = "[Chain of Relationships]"
    final_tag = "[Final Answer]"

    # 1) Presence and exactness
    chain_count = _count_occurrences(response, chain_tag)
    final_count = _count_occurrences(response, final_tag)

    if chain_count == 0:
        # If a near-miss exists (wrong casing), point it out.
        if _exists_case_insensitive(response, chain_tag):
            return (
                False,
                "Use the exact identifier with correct casing and brackets: '[Chain of Relationships]'. "
                "It is currently present with a different casing or format. Insert it exactly as shown."
            )
        return (
            False,
            "Missing required identifier '[Chain of Relationships]'. "
            "Add a section labeled exactly '[Chain of Relationships]' to introduce your reasoning."
        )

    if final_count == 0:
        if _exists_case_insensitive(response, final_tag):
            return (
                False,
                "Use the exact identifier with correct casing and brackets: '[Final Answer]'. "
                "It is currently present with a different casing or format. Insert it exactly as shown."
            )
        return (
            False,
            "Missing required identifier '[Final Answer]'. "
            "Add a section labeled exactly '[Final Answer]' to present your final result."
        )

    # 2) Uniqueness
    if chain_count > 1:
        return (
            False,
            "The identifier '[Chain of Relationships]' appears more than once. "
            "Include each required identifier exactly once to clearly separate sections."
        )

    if final_count > 1:
        return (
            False,
            "The identifier '[Final Answer]' appears more than once. "
            "Include each required identifier exactly once to clearly separate sections."
        )

    # 3) Order
    chain_idx = response.find(chain_tag)
    final_idx = response.find(final_tag)
    if chain_idx > final_idx:
        return (
            False,
            "The identifiers are in the wrong order. "
            "Place '[Chain of Relationships]' before '[Final Answer]'."
        )

    # 4) Non-empty content checks
    chain_content = response[chain_idx + len(chain_tag): final_idx].strip()
    final_content = response[final_idx + len(final_tag):].strip()

    if not _has_alphanumeric(chain_content):
        return (
            False,
            "The section after '[Chain of Relationships]' is empty or lacks substantive text. "
            "Provide a clear, concise explanation of the reasoning between the two identifiers."
        )

    if not _has_alphanumeric(final_content):
        return (
            False,
            "The section after '[Final Answer]' is empty or lacks substantive text. "
            "Provide the final result directly after '[Final Answer]'."
        )

    # Passed all checks
    return (
        True,
        "Valid: both identifiers are present exactly once, in the correct order, with non-empty sections."
    )

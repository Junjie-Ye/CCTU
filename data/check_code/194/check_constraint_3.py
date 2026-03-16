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
 You must use the provided tools to answer the question, ensuring that the tool `historical_infrastructure_info` is called before the tool `historical_event_retriever`, and the tool `literary_author_identifier` is called before the tool `historical_residence_finder`. Additionally, the agent may invoke the `advanced_calculator` tool at most 2 times and the `historical_infrastructure_info` tool at most 2 times. The total number of interaction rounds (tool calls) must not exceed 12. In at least one turn, the agent must invoke at least 2 unique tools simultaneously to improve efficiency. Do not answer the question directly; instead, use the tools to derive the answer step by step. The final answer must begin with the exact phrase: "The number of years passed is: " followed by the result in numerical form, and must end with a period.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', "The number of years passed is: <result> (Mandates that the agent's response must begin with this specific phrase followed by the computed result in numerical form, ensuring a consistent and recognizable opening for the final answer.)")
- idx 3: ('Response', 'Punctuation', 'Ending punctuation (must end with a period.)')
"""

# -*- coding: utf-8 -*-
"""
Validators for response constraints:
- identifiers: enforce required opening phrase and a numeric result immediately after it.
- punctuation: enforce the response ends with a period.
"""

import re
from typing import Tuple

# Constant for the required opening phrase (includes the trailing space)
REQUIRED_PREFIX = "The number of years passed is: "

# Precompiled regex for a numeric value (integer or decimal) at the start of a string
NUMERIC_AT_START_RE = re.compile(r'^(\d+(?:\.\d+)?)\b')


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'identifiers' response constraint:
    - The response must begin with the exact phrase: "The number of years passed is: "
      (including capitalization, punctuation, and the trailing space).
    - Immediately after this phrase, there must be a numeric result (integer or decimal),
      written in digits (no words, units, or commas before the number).

    Returns:
        (is_valid, message)
        message is an English explanation describing how to fix violations.
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string. Provide a string that starts with "
            "'The number of years passed is: ' followed by the numeric result."
        )

    if not response.startswith(REQUIRED_PREFIX):
        return (
            False,
            "Your final answer must start with the exact phrase: 'The number of years passed is: ' "
            "(including the trailing space and exact casing). Do not include any preamble. "
            "Example: 'The number of years passed is: 17.'"
        )

    # Examine the content immediately after the required prefix
    after_prefix = response[len(REQUIRED_PREFIX):]

    # Allow incidental leading spaces after the required space (robustness),
    # but still require the number to appear immediately after any such spaces.
    after_prefix_stripped = after_prefix.lstrip()
    match = NUMERIC_AT_START_RE.match(after_prefix_stripped)

    if not match:
        return (
            False,
            "Immediately after the required prefix, provide the computed result as digits (integer or decimal). "
            "Do not include words, units, or commas before the number. "
            "Examples: 'The number of years passed is: 42.' or 'The number of years passed is: 3.5.'"
        )

    # Additional guidance against commas within numbers (e.g., "1,234")
    # If the first non-space char is a digit but includes a comma before the first non-digit boundary,
    # the regex would fail. We offer a specific hint if a comma is present early on.
    if after_prefix_stripped and after_prefix_stripped[0].isdigit() and "," in after_prefix_stripped.split()[0]:
        return (
            False,
            "Use plain digits without separators. Replace any commas in the number. "
            "For example, use '1234' instead of '1,234'."
        )

    return (
        True,
        "Identifiers requirement satisfied: the response starts with the required phrase and a numeric result."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates the 'punctuation' response constraint:
    - The response must end with a period as the last visible character
      (trailing whitespace after the period is acceptable but discouraged).

    Returns:
        (is_valid, message)
        message is an English explanation describing how to fix violations.
    """
    if not isinstance(response, str):
        return (
            False,
            "Response must be a string. Ensure the answer ends with a period."
        )

    trimmed = response.rstrip()
    if not trimmed.endswith('.'):
        return (
            False,
            "End the final answer with a period as the last visible character. "
            "Example: 'The number of years passed is: 17.'"
        )

    return (
        True,
        "Punctuation requirement satisfied: the response ends with a period."
    )

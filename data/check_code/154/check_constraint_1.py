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
 If the agent intends to invoke multiple tools, they must be executed concurrently in a single action, specifically 'population_estimator' and 'river_length_calculator'. If the agent intends to invoke multiple tools, there must be at least one interaction turn where at least 2 unique tool types are invoked. The agent may invoke the 'historical_infrastructure_designer_finder' tool at most 2 times. The response must end with a period to ensure proper sentence closure and must begin with the phrase 'Answer: ' to clearly identify the start of the response.

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', '(Response, Punctuation, "The response must end with a period to ensure proper sentence closure.")')
- idx 3: ('Response', 'Identifiers', "(Response, Start identifier, The agent's response must begin with the phrase 'Answer: ' to clearly identify the start of the response.)")
"""

import re
from typing import Tuple

# Helper functions


def _last_non_ws_char(s: str) -> str:
    """Return the last non-whitespace character of s, or empty string if none."""
    s = s.rstrip()
    return s[-1] if s else ""


def _has_exact_start_identifier(s: str) -> bool:
    """Check if the response starts exactly (at index 0) with 'Answer: '."""
    return s.startswith("Answer: ")


def _has_start_identifier_after_ws(s: str) -> bool:
    """Check if, after stripping leading whitespace, the response starts with 'Answer: '."""
    return s.lstrip().startswith("Answer: ")


def _starts_with_answer_without_space(s: str) -> bool:
    """Check if the response starts with 'Answer:' but is missing the required trailing space."""
    return s.startswith("Answer:") and not s.startswith("Answer: ")

# Validators for the specified response constraints


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    Constraint: 'The response must end with a period to ensure proper sentence closure.'
    """
    if not isinstance(response, str) or len(response) == 0:
        return (
            False,
            "The response is empty. Provide a non-empty response that ends with a single period '.' as the final character."
        )

    last_char = _last_non_ws_char(response)
    if last_char != ".":
        hint = ""
        if last_char in {"!", "?", ";", ":"}:
            hint = f" Replace the final '{last_char}' with a period."
        elif last_char == "":
            hint = " Add a period '.' at the end."
        else:
            hint = " Ensure the final non-whitespace character is a period '.'."
        return (
            False,
            "The response must end with a period '.' as the final non-whitespace character." + hint +
            " Example fix: \"Answer: <your final sentence>.\""
        )

    return (
        True,
        "Punctuation is valid: the response ends with a period '.' as the final non-whitespace character."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response begins with the exact phrase 'Answer: '.
    Constraint: 'The agent's response must begin with the phrase 'Answer: ' to clearly identify the start of the response.'
    """
    if not isinstance(response, str) or len(response) == 0:
        return (
            False,
            "The response is empty. Start the response with exactly 'Answer: ' followed by your content, e.g., \"Answer: ...\"."
        )

    # Exact start at position 0
    if _has_exact_start_identifier(response):
        return (
            True,
            "Identifier is valid: the response begins with the exact phrase 'Answer: '."
        )

    # If it's present after leading whitespace
    if _has_start_identifier_after_ws(response):
        return (
            False,
            "Do not include any leading whitespace or preamble. The response must start at the very first character with exactly 'Answer: ' (including the colon and a single trailing space)."
        )

    # If it starts with 'Answer:' but missing the required trailing space
    if _starts_with_answer_without_space(response):
        return (
            False,
            "After 'Answer:' you must include a single space. Start the response exactly as: 'Answer: '. Example: \"Answer: Your content here.\""
        )

    # If 'Answer:' appears later in the string
    if "Answer:" in response:
        return (
            False,
            "Move the identifier to the very beginning and include a trailing space: start the response with exactly 'Answer: ' followed by your content. No text is allowed before it."
        )

    # Otherwise, the identifier is missing altogether
    return (
        False,
        "Missing required start identifier. Begin the response with exactly 'Answer: ' (including the colon and a single space), e.g., \"Answer: <your final sentence>.\""
    )

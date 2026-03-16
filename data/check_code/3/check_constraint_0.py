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
 The answer must begin with "ANSWER:" to clearly indicate the start of the response.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'Must begin with "ANSWER:" to clearly indicate the start of the answer.')
"""

from typing import Tuple
import re

EXACT_PREFIX = "ANSWER:"


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response begins exactly with the identifier 'ANSWER:'.

    Rules enforced:
    - The very first characters of the response (position 0) must be the exact uppercase string 'ANSWER:'.
    - No leading whitespace or any other content is allowed before 'ANSWER:'.
    - Case must be uppercase exactly as 'ANSWER:' (not 'Answer:' or 'answer:').

    Returns:
        (is_valid, message)
        - is_valid: True if the response meets the requirement; otherwise False.
        - message: Detailed English guidance on how to fix the response if invalid.
    """
    if not isinstance(response, str):
        return (
            False,
            "The response must be a string. Provide a string that begins exactly with 'ANSWER:' at position 0."
        )

    # Fast-path: exact required prefix at position 0
    if response.startswith(EXACT_PREFIX):
        return True, "Valid: response begins with 'ANSWER:' at position 0."

    # Detect if 'ANSWER:' appears but not at position 0
    idx_exact_anywhere = response.find(EXACT_PREFIX)
    if idx_exact_anywhere > 0:
        return (
            False,
            "Place 'ANSWER:' at the very beginning of the response. Do not include any characters (including spaces or newlines) before it. "
            f"Currently, 'ANSWER:' starts at index {idx_exact_anywhere}. Move it to index 0 so the response starts with 'ANSWER:'."
        )

    # Detect leading whitespace before a correct token
    if re.match(r"^\s+ANSWER:", response):
        leading_ws = re.match(r"^\s+", response).group(0)
        return (
            False,
            f"Remove the leading whitespace before 'ANSWER:'. The response must start exactly with 'ANSWER:' at position 0. "
            f"Detected {len(leading_ws)} leading whitespace characters."
        )

    # Detect case-insensitive 'answer:' at start
    if re.match(r"^answer\s*:", response, flags=re.IGNORECASE):
        return (
            False,
            "Use the exact uppercase identifier 'ANSWER:' at the very beginning. Replace the current prefix with 'ANSWER:' (all caps, followed by a colon)."
        )

    # Detect presence of a similar token anywhere (case-insensitive)
    m_anywhere = re.search(r"answer\s*:", response, flags=re.IGNORECASE)
    if m_anywhere:
        return (
            False,
            "Begin the response with the exact token 'ANSWER:' at position 0. Do not include any preceding text. "
            "Ensure it is uppercase exactly as 'ANSWER:' followed by a colon."
        )

    # Generic failure: prefix missing entirely
    snippet = response[:40].replace("\n", "\\n")
    return (
        False,
        "Prepend the exact token 'ANSWER:' (uppercase, followed by a colon) to the very beginning of the response. "
        "Example: 'ANSWER: <your content>'. Current beginning: '" + snippet + "'."
    )

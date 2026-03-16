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
 Your response must end with the country name enclosed in double asterisks to indicate the final answer and must end with a period (.) to ensure proper sentence closure. Additionally, **if the agent intends to invoke the geopolitical_event_finder tool**, the maximum number of invocations must not exceed three, and the final answer must be concise, containing at most 20 words.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'Must include the country name within double asterisks at the end of the response to denote the final answer')
- idx 2: ('Response', 'Punctuation', 'Must end with a period (.) to indicate proper sentence closure')
"""

import re
from typing import Tuple

# Helper: return the string without trailing whitespace


def _rstrip(s: str) -> str:
    return s.rstrip()


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period (.)
    - Ignores trailing whitespace.
    """
    trimmed = _rstrip(response)
    if not trimmed:
        return False, "The response is empty. Provide a non-empty answer that ends with a single period (e.g., '... **Country**.')."
    if trimmed[-1] != ".":
        return False, (
            "Your response must end with a single period. Add one final '.' at the very end (after '**Country**'). "
            "Example: '... **Country**.'"
        )
    return True, "Punctuation is valid: the response ends with a period."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the country name enclosed in double asterisks.
    This expects the final token (before the terminal period, if any) to be: **Country Name**
    Acceptable endings:
      - '... **Country**.'
      - '... **Country**'  (period is checked separately by the punctuation validator)
    """
    trimmed = _rstrip(response)

    # If there is a final period, ignore it for the identifier check.
    if trimmed.endswith("."):
        base = _rstrip(trimmed[:-1])
    else:
        base = trimmed

    # Must end with **...** at the very end (no extra characters after).
    m_end = re.search(r"\*\*([^*]+)\*\*$", base)
    if m_end:
        name = m_end.group(1).strip()
        if not name:
            return False, (
                "The content between the final double asterisks is empty. Replace it with the actual country name, "
                "e.g., '**Kenya**.'"
            )
        return True, "Identifiers are valid: the response ends with a double-asterisk-wrapped country name."
    else:
        # Diagnose common mistakes to give precise guidance.
        m_any = re.search(r"\*\*([^*]+)\*\*", base)
        if m_any:
            return False, (
                "The country name wrapped in double asterisks is not at the end. Move '**{name}**' to the very end, "
                "right before the final period. Example: '... **{name}**.'"
            ).format(name=m_any.group(1).strip())
        return False, (
            "Your response must end with the country name enclosed in double asterisks. Place '**Country**' at the very end, "
            "followed by a period. Example: '... **Country**.'"
        )

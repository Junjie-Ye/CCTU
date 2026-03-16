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
 The solution must use parallel execution: in at least one interaction turn, the agent must invoke between 1 and 2 unique tool types simultaneously (e.g., calling the same tool twice counts as one unique type, while calling two different tools counts as two). The agent must never exceed two unique tool types in any single turn. The solution must be completed within a total of 2 to 3 interaction turns. Additionally, the final answer must conclude with the identifier "[END OF ANSWER]" to clearly indicate the end of the response and end with a period (.) to ensure proper sentence closure. The agent may invoke the `unified_specification_retriever` tool at most 2 times in total to prevent over-reliance on a single tool for data retrieval. No other tool may be used more than once in this task.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', "(Response, End identifier, The agent's response must conclude with the identifier '[END OF ANSWER]' followed by a punctuation mark to indicate the completion of the answer.)")
- idx 4: ('Response', 'Punctuation', "The agent's response must end with a period (.) to ensure proper sentence closure.")
"""

import re
import string
from typing import Tuple

# Helper constants
END_IDENTIFIER = "[END OF ANSWER]"

# Helper: check if a single character is (ASCII) punctuation


def _is_single_punctuation_char(ch: str) -> bool:
    return len(ch) == 1 and ch in string.punctuation

# Helper: right-trim whitespace for consistent end checks


def _rtrim(s: str) -> str:
    return s.rstrip()


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the required end identifier
    followed immediately by a punctuation mark, with no extra characters after it.
    Requirement:
      - The agent's response must conclude with the identifier "[END OF ANSWER]"
        followed by a punctuation mark to indicate completion.
    Notes:
      - Trailing whitespace is ignored.
      - There must be exactly one punctuation character immediately after the identifier
        and then the string must end (no extra characters).
    """
    trimmed = _rtrim(response)

    if not trimmed:
        return (
            False,
            'The response is empty. Conclude the response with "[END OF ANSWER]" followed immediately by a punctuation mark (e.g., "[END OF ANSWER].").'
        )

    last_idx = trimmed.rfind(END_IDENTIFIER)
    if last_idx == -1:
        return (
            False,
            'Missing end identifier. Append the exact token "[END OF ANSWER]" at the very end of the response, immediately followed by a punctuation mark (e.g., end with "[END OF ANSWER].").'
        )

    # Ensure we're validating the last occurrence and that it is at the very end
    after = trimmed[last_idx + len(END_IDENTIFIER):]

    if last_idx + len(END_IDENTIFIER) < len(trimmed):
        # There are characters after the identifier in this last occurrence
        if len(after) == 1 and _is_single_punctuation_char(after):
            # This is acceptable only if this is the very end; since 'after' is the final slice and trimmed has no trailing spaces,
            # this means it already ends with exactly one punctuation.
            return (
                True,
                'Valid: the response ends with the required identifier followed by a punctuation mark.'
            )
        else:
            return (
                False,
                'The end identifier must be the final token, immediately followed by exactly one punctuation mark and nothing else. '
                'Revise the ending to have no extra spaces or characters after the punctuation, e.g., "... [END OF ANSWER]."'
            )
    else:
        # Ends exactly with the identifier and no punctuation
        return (
            False,
            'The response ends with the identifier but lacks the required punctuation mark. '
            'Insert exactly one punctuation character immediately after the closing bracket. '
            'Given the separate punctuation constraint, use a period: end with "[END OF ANSWER]."'
        )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' to ensure proper sentence closure.
    Requirement:
      - The agent's response must end with a period (.)
    Notes:
      - Trailing whitespace is ignored for validation.
      - If the response includes the "[END OF ANSWER]" identifier at the end, the period must come immediately after it,
        forming the exact ending: "[END OF ANSWER]."
    """
    trimmed = _rtrim(response)

    if not trimmed:
        return (
            False,
            'The response is empty. Ensure the final character of the response is a period ".", e.g., end with "[END OF ANSWER].".'
        )

    if trimmed.endswith('.'):
        return (
            True,
            'Valid: the response ends with a period.'
        )

    # Provide targeted guidance depending on the current ending
    if trimmed.endswith(END_IDENTIFIER):
        return (
            False,
            'Add a period immediately after the end identifier so the response ends with the exact sequence "[END OF ANSWER]." with no extra text after.'
        )

    if re.search(r'[!?;:,]$', trimmed):
        last = trimmed[-1]
        return (
            False,
            f'The response currently ends with "{last}". Replace the final punctuation with a period "." so it ends correctly. '
            'If you use the end identifier, the final characters must be "[END OF ANSWER]."'
        )

    return (
        False,
        'The response does not end with a period. Append a period "." as the very last character. '
        'If you include the end identifier, ensure the exact ending is "[END OF ANSWER]." with no additional characters after the period.'
    )

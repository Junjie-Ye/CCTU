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

r"""
refine_constraint:
 You must use at most 8 tool calls to solve this, your response must end with the final answer enclosed in a box, e.g., **Final Answer:** $\boxed{\{numeric\}}$, and your explanation must be at least 50 characters long.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'Must end with the final answer enclosed in a box, e.g., **Final Answer:** $\\\\boxed{\\\\{numeric\\\\}}$')
"""

import re
from typing import Tuple

# Helper: check if a string is a valid numeric literal (int, float, or scientific notation).
_NUMERIC_RE = re.compile(r"^\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?\s*$")


def _extract_box_content(segment: str) -> Tuple[bool, str]:
    """
    Try to extract content inside \boxed{...} from a segment and validate numeric.
    Returns (is_valid_numeric, extracted_content or "").
    """
    m = re.search(r"\\boxed\{\s*(.*?)\s*\}", segment, flags=re.DOTALL)
    if not m:
        return False, ""
    inner = m.group(1)
    return bool(_NUMERIC_RE.match(inner)), inner


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the final answer enclosed in a LaTeX box,
    exactly in the format: **Final Answer:** $\boxed{<numeric>}$

    Rules enforced:
    - The final segment must be at the very end of the response (allowing trailing whitespace).
    - The segment must start with the literal '**Final Answer:**'.
    - The numeric result must be the ONLY content inside \boxed{...}.
    - The \boxed{...} must be wrapped in math delimiters with starting '$' and ending '$'.
    """
    # Pattern for the exact required ending (allow trailing whitespace after the closing $).
    ending_re = re.compile(
        r"\*\*Final Answer:\*\*\s*\$\s*\\boxed\{\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*\}\s*\$\s*$",
        flags=re.MULTILINE
    )
    if ending_re.search(response):
        return True, "Valid: response ends with '**Final Answer:** $\\boxed{<numeric>}$' and contains a numeric result."

    # If not valid, build targeted guidance.
    msg_parts = []

    # Check for presence of the final answer tag.
    tag = "**Final Answer:**"
    idx = response.rfind(tag)
    if idx == -1:
        msg_parts.append(
            "Missing the final tag. Append a final line exactly as: "
            "**Final Answer:** $\\boxed{<numeric>}$"
        )
        msg_parts.append(
            "Place this segment at the very end of your response (no content after it)."
        )
        return False, " ".join(msg_parts)

    # Examine the tail starting from the tag to the end.
    tail = response[idx:]
    tail_stripped_end = tail.rstrip()

    # Ensure math delimiters are present and correctly closed.
    if not re.search(r"\$\s*\\boxed", tail):
        msg_parts.append(
            "Missing opening math delimiter before \\boxed. Use: '$\\boxed{...}$'."
        )
    if not tail_stripped_end.endswith("$"):
        msg_parts.append(
            "Missing closing '$' after the boxed result. Ensure the segment ends with '$'."
        )

    # Ensure \boxed{...} exists.
    if not re.search(r"\\boxed\{.*\}", tail, flags=re.DOTALL):
        msg_parts.append(
            "Missing '\\boxed{...}'. Enclose the numeric result inside \\boxed{<numeric>}."
        )
    else:
        is_num, inner = _extract_box_content(tail)
        if not is_num:
            msg_parts.append(
                "Non-numeric content inside \\boxed{...}. Use only a numeric literal "
                "(e.g., 42, -3.14, 6.02e23) with no extra symbols or text."
            )

    # Ensure it is the very end (no text after the closing math).
    end_pattern = re.compile(r"\*\*Final Answer:\*\*.*\$\s*$", flags=re.DOTALL)
    if not end_pattern.search(response):
        msg_parts.append(
            "The final answer segment must be the last content. Remove any text after "
            "'**Final Answer:** $\\boxed{<numeric>}$'."
        )

    # Provide a concise corrective template.
    msg_parts.append(
        "Correct template: **Final Answer:** $\\boxed{123}$ "
        "(replace 123 with your numeric result)."
    )

    return False, " ".join(msg_parts)

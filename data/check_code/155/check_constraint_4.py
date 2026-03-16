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
 The solution must ensure that the 'business_location_finder' tool is called before the 'country_info_retriever' tool, the total number of interaction turns must be between 10 and 12 inclusive, **if the agent intends to invoke both 'country_info_retriever' and 'geographical_feature_associator', they must be executed concurrently in a single action step** after confirming the target country and associated region, and the final answer must conclude with the exact phrase "Final Answer: " followed by the numerical result in bold. The final answer must be concise and not exceed 1000 characters.

response_constraints_non_length:
- idx 4: ('Response', 'Identifiers', '(Response, End identifier, The agent\'s final answer must conclude with the exact phrase "Final Answer: " followed by the numerical result in bold, ensuring a standardized and recognizable conclusion to the response.)')
"""

import re
from typing import Tuple

# Precompiled regex for the exact required end-identifier pattern:
# Must end with: Final Answer: **<number>**
# <number> can be:
# - integer with optional leading sign, with or without thousands separators (e.g., 1234 or 1,234)
# - decimal (e.g., 123.45 or .75)
# - scientific notation (e.g., 1.2e-3, -3E+5)
FINAL_ANSWER_EXACT_RE = re.compile(
    r'Final Answer: \*\*'
    r'(?P<num>'
    r'[-+]?('
    r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'  # 1,234 or 1234 or with decimal
    r'|'
    r'\.\d+'                                  # .5
    r')'
    r'(?:[eE][-+]?\d+)?'                      # optional exponent
    r')'
    # must end (allow trailing whitespace)
    r'\*\*\s*$',
    re.MULTILINE
)

NUMERIC_ONLY_RE = re.compile(
    r'^[-+]?(?:'
    r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
    r'|\.\d+'
    r')(?:[eE][-+]?\d+)?$'
)


def _last_nonempty_line(text: str) -> str:
    lines = text.rstrip().splitlines()
    for line in reversed(lines):
        if line.strip():
            return line
    return ""


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the exact end identifier:
    'Final Answer: ' followed by the numerical result in bold, i.e., Final Answer: **<number>**,
    with no characters after the closing '**' (trailing whitespace allowed).
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty. End the response with: Final Answer: **<number>** where <number> is numeric."
        )

    trimmed = response.rstrip()

    # Fast-path: exact match at the end
    if FINAL_ANSWER_EXACT_RE.search(trimmed):
        return (
            True,
            "Valid: The response ends with the required pattern 'Final Answer: **<number>**'."
        )

    # Construct detailed diagnostics
    issues = []
    last_line = _last_nonempty_line(trimmed)

    if "Final Answer" not in trimmed:
        issues.append(
            "Missing the required end identifier line starting with 'Final Answer: '.")
        example = "Example: Final Answer: **42**"
        guidance = (
            "Add a final line exactly as: Final Answer: **<number>** "
            "with one space after the colon, bold markers '**', and no text after the closing '**'."
        )
        return (False, f"{' '.join(issues)} {guidance} {example}")

    # Check last line formatting
    if not last_line.startswith("Final Answer"):
        issues.append(
            "The final non-empty line must be the end identifier starting with 'Final Answer: '.")
    else:
        if last_line.startswith("Final Answer:") and not last_line.startswith("Final Answer: "):
            issues.append(
                "Insert exactly one space after the colon: 'Final Answer: ' (note the single space).")
        if last_line.startswith("Final Answer: "):
            rest = last_line[len("Final Answer: "):]
            if not rest.startswith("**"):
                issues.append(
                    "Bold the numeric result using '**' immediately after 'Final Answer: '. Example: Final Answer: **123**.")
            else:
                # Try to capture **...**
                m = re.match(r'^\*\*(.*?)\*\*(.*)$', rest)
                if not m:
                    issues.append(
                        "Close the bold markup with '**' after the number. Example: Final Answer: **123**.")
                else:
                    bold_content = m.group(1)
                    trailing = m.group(2)
                    if not NUMERIC_ONLY_RE.fullmatch(bold_content):
                        issues.append(
                            "The bolded content must be a bare numeric value (e.g., 42, -1, 1,234.56, 3e-5). "
                            "Do not include units, words, or currency symbols."
                        )
                    if trailing.strip():
                        issues.append(
                            "Remove any characters after the closing '**'; nothing may follow the bold number.")

    if not issues:
        issues.append(
            "End the response exactly with: Final Answer: **<number>**. "
            "Ensure correct spacing, bold markers, and that <number> is numeric."
        )

    return (
        False,
        " ".join(issues) + " Example: Final Answer: **42**"
    )

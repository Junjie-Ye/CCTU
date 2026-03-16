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
 You must obtain the answer by calling the provided tools. If a tool call fails, you may retry, but the total number of tool calls across all interaction turns must not exceed 3. The final answer must be enclosed in a box (e.g., $$\n\\boxed{\\text{...}}\n$$) and must be between 10 and 20 words in length.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Response, Delimiting identifier, Must include the final answer enclosed in a box (e.g., $$\\n\\\\boxed{\\\\text{...}}\\n$$))')
"""

import re
from typing import Tuple, List

# Helper regex to detect the boxed LaTeX final answer block:
# Matches: $$ [optional newline/whitespace] \boxed{ \text{ ... } } [optional newline/whitespace] $$
BOXED_PATTERN = re.compile(
    r'\$\$\s*(?:\n\s*)?\\boxed\{\s*\\text\{(.+?)\}\s*\}\s*(?:\n\s*)?\$\$',
    re.DOTALL
)


def _find_boxed_segments(response: str) -> List[re.Match]:
    """
    Find all boxed final answer segments of the form:
    $$\n\\boxed{\\text{...}}\n$$
    Returns list of regex match objects for further position checks.
    """
    return list(BOXED_PATTERN.finditer(response))


def _has_trailing_non_whitespace(response: str, end_index: int) -> bool:
    """
    Check if there is any non-whitespace character after the given end_index.
    """
    trailing = response[end_index:]
    return bool(re.search(r'\S', trailing))


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates that the final answer is enclosed using the required delimiting identifier:
    A single LaTeX boxed block exactly in the form:
    $$\n\\boxed{\\text{...}}\n$$

    Rules enforced:
    - There must be exactly one boxed block matching the pattern with \\boxed and \\text.
    - The boxed block must be the last non-whitespace content in the response.
    - Double dollar signs $$ must be used (not single $).
    - The inner content must be inside \\text{...} within \\boxed{...}.

    Returns:
        (bool, str): A tuple where bool indicates compliance, and str provides
        detailed English guidance on how to fix issues if any.
    """
    matches = _find_boxed_segments(response)

    if len(matches) == 0:
        return (
            False,
            "Missing required boxed final answer. Add exactly one block using double dollar signs and LaTeX boxing:\n"
            "Example:\n"
            "$$\n\\boxed{\\text{YOUR 10–20 WORD FINAL ANSWER HERE}}\n$$\n"
            "Requirements:\n"
            "- Use $$ (double dollar signs) before and after the block.\n"
            "- Use \\boxed{\\text{...}} with your final answer inside \\text{...}.\n"
            "- Place this boxed block as the last non-whitespace content in your response.\n"
            "- Do not include additional text after the closing $$."
        )

    if len(matches) > 1:
        return (
            False,
            "Multiple boxed blocks detected. Provide exactly one final answer block:\n"
            "Keep only a single instance of:\n"
            "$$\n\\boxed{\\text{YOUR FINAL ANSWER}}\n$$\n"
            "Remove any extra \\boxed or $$ blocks and ensure the remaining one is the last non-whitespace content."
        )

    # Exactly one match
    match = matches[0]
    start, end = match.span()

    # Check for trailing non-whitespace after the boxed block
    if _has_trailing_non_whitespace(response, end):
        return (
            False,
            "Extra content found after the boxed final answer. The boxed block must be the last non-whitespace content.\n"
            "Move any additional text before the block or remove it.\n"
            "Final lines should end exactly with:\n"
            "$$\n\\boxed{\\text{YOUR FINAL ANSWER}}\n$$"
        )

    # Additional structural guidance: ensure \text{...} is present (already enforced by regex),
    # but provide clarity in success message.
    return (
        True,
        "Identifiers constraint satisfied: exactly one $$\\boxed{\\text{...}}$$ block found and placed at the end."
    )

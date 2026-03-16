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
 Your response must conclude with the phrase "$$\n\\boxed{\\text{[Target Religion]}}\n$$" to indicate the final answer clearly, and the AI agent must use at most three tool calls to solve this problem.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', '(Response, End identifier, "The response must conclude with the phrase \'$$\\n\\\\boxed{\\\\text{[Target Religion]}}\\n$$\'.")')
"""

import re
from typing import Tuple

# Helper compiled regex patterns for the required end identifier.
# We accept two variants:
# 1) The practical LaTeX form with single backslashes:
#    $$
#    \boxed{\text{[Target Religion]}}
#    $$
# 2) A literal-escaped variant with doubled backslashes (to be tolerant of some generators).
# Capture any non-empty, single-line target inside \text{...}
SINGLE_BSLASH_END = re.compile(
    r"\$\$\r?\n\\boxed\{\\text\{([^\r\n{}]+)\}\}\r?\n\$\$\Z",
    re.MULTILINE,
)
DOUBLE_BSLASH_END = re.compile(
    r"\$\$\r?\n\\\\boxed\{\\\\text\{([^\r\n{}]+)\}\}\r?\n\$\$\Z",
    re.MULTILINE,
)

SINGLE_BSLASH_ANYWHERE = re.compile(
    r"\$\$\r?\n\\boxed\{\\text\{([^\r\n{}]+)\}\}\r?\n\$\$",
    re.MULTILINE,
)
DOUBLE_BSLASH_ANYWHERE = re.compile(
    r"\$\$\r?\n\\\\boxed\{\\\\text\{([^\r\n{}]+)\}\}\r?\n\$\$",
    re.MULTILINE,
)


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the exact required phrase:
    $$
    \boxed{\text{[Target Religion]}}
    $$
    The check is tolerant to optional trailing whitespace in the response and
    accepts either single-backslash LaTeX or a double-backslash (escaped) variant.
    """
    # Ignore trailing whitespace for the "conclude with" requirement.
    trimmed = response.rstrip()

    # Check if the required phrase is exactly at the end.
    if SINGLE_BSLASH_END.search(trimmed) or DOUBLE_BSLASH_END.search(trimmed):
        return (
            True,
            "Pass: The response ends with the required LaTeX phrase. "
            "Ensure there are no characters after the closing '$$'."
        )

    # If not at the end, see if the phrase exists somewhere else in the text.
    if SINGLE_BSLASH_ANYWHERE.search(trimmed) or DOUBLE_BSLASH_ANYWHERE.search(trimmed):
        return (
            False,
            "Fail: The required closing phrase exists but is not the final content. "
            "Move it to the very end and remove any characters (including punctuation or code fences) after it. "
            "The final lines must be exactly:\n"
            "$$\n\\boxed{\\text{[Target Religion]}}\n$$"
        )

    # Phrase not found at all.
    return (
        False,
        "Fail: The response does not end with the required closing phrase. "
        "Your final output must conclude exactly with the following (no characters after it; include the newlines):\n"
        "$$\n\\boxed{\\text{[Target Religion]}}\n$$\n"
        "Prefer the LaTeX form with single backslashes (as shown). Do not add trailing spaces or extra text after the closing '$$'."
    )

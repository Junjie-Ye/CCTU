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
 You must determine this by calling the available tools, ensuring that the total number of tool calls is between 5 and 10 and that the total number of interaction turns is between 5 and 12. Your response must conclude with the exact phrase "The local fish in the area is: [Species]" to ensure a standardized and recognizable ending, and must not exceed 100 words in total.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "The answer must conclude with the exact phrase 'The local fish in the area is: [Species]' to ensure a standardized and recognizable ending.")
"""

import re
from typing import Tuple

REQUIRED_PREFIX = "The local fish in the area is: "
TRAILING_PUNCTUATION = set(".!?,;:。!?;,、)›»]”’\"'")


def _rstrip_preserve_core(s: str) -> str:
    return s.rstrip()


END_PATTERN = re.compile(rf"{re.escape(REQUIRED_PREFIX)}([^\r\n]+)\Z")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with:
    'The local fish in the area is: <Species>'
    - Prefix must match exactly (case/spacing/punctuation)
    - Species can be any non-empty single-line string
    - No extra characters after species (except trailing whitespace)
    """
    s = _rstrip_preserve_core(response)

    m = END_PATTERN.search(s)
    if m:
        species = m.group(1).strip()
        if not species:
            return (
                False,
                "The species name is missing. End with: 'The local fish in the area is: <Species>' (non-empty)."
            )
        if species[-1] in TRAILING_PUNCTUATION:
            return (
                False,
                "Do not add punctuation after the species. The final non-whitespace character must be part of the species name."
            )
        return True, "Pass: The response ends with the required prefix and a valid species."

    if REQUIRED_PREFIX in s:
        idx = s.rfind(REQUIRED_PREFIX)
        after = s[idx + len(REQUIRED_PREFIX):]
        if not after.strip():
            return (
                False,
                "The species name is missing after the prefix. Provide a non-empty species name."
            )
        return (
            False,
            "Ensure the very end of the response is exactly: "
            "'The local fish in the area is: <Species>' with no extra text after it."
        )

    if s.lower().endswith(REQUIRED_PREFIX.lower()):
        return (
            False,
            f"Use the exact casing/spacing: '{REQUIRED_PREFIX}<Species>'."
        )

    return (
        False,
        f"Append the required ending at the end: '{REQUIRED_PREFIX}<Species>' (prefix must match exactly)."
    )

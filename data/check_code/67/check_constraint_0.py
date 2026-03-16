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
 You must use tool calls to answer this question, and you can make at most 10 tool calls. The response must strictly conclude with the specific phrase 'The traditional hat is: [result].', where '[result]' is replaced by the actual name of the hat identified. If the agent intends to invoke the `cultural_artifact_identifier`, the `biographical_info_retriever` must strictly be executed beforehand. If the agent intends to invoke the `biographical_info_retriever`, the `geographer_identifier` must strictly be executed beforehand. If the agent intends to invoke the `geographer_identifier`, the `river_source_locator` must strictly be executed beforehand. If the agent intends to invoke the `river_source_locator`, the `river_locator` must strictly be executed beforehand. If the agent intends to invoke the `river_locator`, the `institution_location_finder` must strictly be executed beforehand. If the agent intends to invoke the `institution_location_finder`, the `academic_institution_locator` must strictly be executed beforehand. If the agent intends to invoke the `academic_institution_locator`, the `academic_founder_identifier` must strictly be executed beforehand.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "The response must strictly conclude with the specific phrase 'The traditional hat is: [result].', where '[result]' is replaced by the actual name of the hat identified.")
- idx 2: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
"""

import re
from typing import Tuple

# Precompiled regex to validate the required closing phrase.
# It enforces that the response ends (optionally after whitespace) with:
# "The traditional hat is: <result>."
# where <result> is at least one non-empty sequence (captured lazily), and the final character is a period.
CLOSING_PHRASE_RE = re.compile(
    r"The traditional hat is:\s*(?P<result>.+?)\.\s*$",
    flags=re.DOTALL
)


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period as the last non-whitespace character.
    Returns:
      (True, message) if valid,
      (False, message) with detailed correction guidance if invalid.
    """
    if not isinstance(response, str):
        return False, "Response must be a string. Provide a string that ends with a period."
    stripped = response.rstrip()
    if not stripped:
        return False, "The response is empty. Provide a sentence that ends with a single period '.' as the last character."
    if stripped.endswith('.'):
        return True, "OK: The response ends with a period."
    return (
        False,
        "The response must end with a period '.' as the final printable character. "
        "Remove any trailing quotes, emojis, or other characters after the period. "
        "Example: The traditional hat is: Panama hat."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response strictly concludes with the exact phrase pattern:
    'The traditional hat is: [result].' where [result] is replaced by the actual hat name.
    Requirements:
      - The phrase must appear at the very end of the response (only trailing whitespace allowed).
      - Use exact casing and punctuation for 'The traditional hat is:' including the colon.
      - Replace [result] with a non-empty name (no square brackets).
      - No text is allowed after the final period (except whitespace).
    Returns:
      (True, message) if valid,
      (False, message) with detailed correction guidance if invalid.
    """
    if not isinstance(response, str):
        return False, "Response must be a string. Conclude with: The traditional hat is: <Name>."
    m = CLOSING_PHRASE_RE.search(response)
    if not m:
        return (
            False,
            "Your answer must strictly conclude with the phrase: 'The traditional hat is: [result].' "
            "Use the exact casing and punctuation, place a colon after 'is', and end with a single period. "
            "Only whitespace may follow the period. Example: The traditional hat is: Panama hat."
        )
    result = m.group("result").strip()
    # Check that [result] is actually replaced (no square brackets or empty content).
    if not result:
        return (
            False,
            "Replace [result] with a non-empty hat name after the colon. Example: The traditional hat is: Panama hat."
        )
    if '[' in result or ']' in result:
        return (
            False,
            "Do not include square brackets in the result. Replace them with the actual hat name. "
            "Example: The traditional hat is: Panama hat."
        )
    # Ensure the result looks like a plausible name: must contain at least one letter.
    # (Prevents placeholders like '---' or purely numeric content.)
    if not re.search(r'[A-Za-z]', result):
        return (
            False,
            "The [result] must contain alphabetic characters of the hat name. "
            "Use a readable name with letters (and optional spaces/hyphens/apostrophes). "
            "Example: The traditional hat is: Panama hat."
        )
    return True, "OK: The response correctly concludes with 'The traditional hat is: [result].' and a valid result name."

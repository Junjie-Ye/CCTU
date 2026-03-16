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
 If the agent invokes `literary_verse_finder`, it is strictly required to also utilize `event_city_identifier` simultaneously. Furthermore, the `park_feature_locator` tool can only be legitimately invoked if `biographical_data_retriever` has already been executed. All other steps must follow logically and adhere to the constraint that all information must be obtained via tool calls, with the agent correcting any errors and retrying until a valid solution is reached. Additionally, the final response must include the keyword "Delimiting Identifier: [Comparison Result]" to clearly separate the final answer from the reasoning. The final response must be between 300 and 500 characters in length, measured in characters, to ensure clarity and completeness without unnecessary verbosity. The final answer must end with an exclamation mark (!) to emphasize the conclusion.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', 'The response must include the keyword "Delimiting Identifier: [Comparison Result]" to clearly separate the final answer from the reasoning.')
- idx 4: ('Response', 'Punctuation', 'The final answer must end with an exclamation mark (!) to emphasize the conclusion.')
"""

import re
from typing import Tuple

# Constant keyword required by the "identifiers" constraint
REQUIRED_KEYWORD = "Thus, here is the answer."


def _last_visible_char(text: str) -> str:
    """
    Return the last non-whitespace character of text, or empty string if none.
    """
    if text is None:
        return ""
    for ch in reversed(text):
        if not ch.isspace():
            return ch
    return ""


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the exact keyword:
    'Delimiting Identifier: [Comparison Result]'
    Additionally, ensure there is non-whitespace content after the keyword,
    indicating that the delimiter actually precedes the final answer.
    """
    if response is None:
        return (
            False,
            "Response is None. Provide a textual response that includes the exact keyword "
            "'Thus, here is the answer.' before the final answer."
        )

    matches = list(re.finditer(re.escape(REQUIRED_KEYWORD), response))
    if not matches:
        return (
            False,
            "Missing required delimiter keyword. Insert the exact, case-sensitive phrase "
            "'Thus, here is the answer.' (including colon, spaces, and square brackets) "
            "immediately before the final answer section. Example:\n"
            "...reasoning...\nDelimiting Identifier: [Comparison Result]\nYour final answer here!"
        )

    # Use the last occurrence as the delimiter for the final answer section
    last_match = matches[-1]
    after = response[last_match.end():].strip()

    if not after:
        return (
            False,
            "The required keyword is present but no content follows it. Place your final answer text "
            "immediately after 'Thus, here is the answer.'. Ensure there is at least one "
            "sentence of content after the keyword."
        )

    return (
        True,
        "Identifier requirement satisfied: the exact keyword is present and followed by content. "
        "Keep the phrase 'Thus, here is the answer.' immediately before the final answer."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final visible character of the response is an exclamation mark '!'.
    Trailing whitespace is ignored, but no other characters may appear after '!'.
    """
    if response is None or not response.strip():
        return (
            False,
            "The response is empty or whitespace-only. Provide a final answer and make the very last "
            "visible character an exclamation mark '!'."
        )

    last_char = _last_visible_char(response)
    if last_char != "!":
        return (
            False,
            "The final visible character must be '!'. Append a single '!' as the very last character "
            "of the message. Move or remove any trailing periods, quotes, emojis, footnotes, or markdown "
            "so that '!' is the final character."
        )

    return (
        True,
        "Punctuation requirement satisfied: the last visible character is '!'."
    )

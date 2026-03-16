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
 Your response must include the exact phrase "[Answer]" immediately before the final sentence that explicitly states the banned vehicle type, the final sentence must end with a period, and the entire response must be between 15 and 50 words in length to ensure clarity and conciseness.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'The agent\'s response must include the exact phrase "[Answer]" immediately before the final sentence containing the banned vehicle type')
- idx 1: ('Response', 'Punctuation', '"The response must end with a period to ensure proper sentence closure."')
"""

import re
from typing import Tuple, Optional


# -----------------------------
# Helper utilities (shared)
# -----------------------------

SENTENCE_PATTERN = re.compile(r'[^.!?]+[.!?]', flags=re.S)
ANSWER_LEADING_PATTERN = re.compile(r'^\s*\[Answer\]\s+\S', flags=re.S)


def _strip_trailing_whitespace(text: str) -> str:
    return text.rstrip()


def _last_nonempty_sentence(text: str) -> Optional[str]:
    """
    Return the last sentence (including its terminal punctuation) if any.
    Sentences are detected by ., !, or ? terminal marks.
    If none found, return the stripped text or None if empty.
    """
    stripped = text.strip()
    if not stripped:
        return None
    sentences = SENTENCE_PATTERN.findall(stripped)
    if sentences:
        # Return last non-empty sentence
        for s in reversed(sentences):
            if s.strip():
                return s
        return None
    # No clear sentence boundaries found; treat entire text as one "sentence"
    return stripped if stripped else None


def _final_char_is_period(text: str) -> bool:
    """
    Check whether the last non-whitespace character is a period.
    """
    stripped = _strip_trailing_whitespace(text)
    return stripped.endswith('.')


# -----------------------------
# Validators
# -----------------------------

def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Punctuation constraint:
    - "The response must end with a period to ensure proper sentence closure."

    Validation:
    - The last non-whitespace character of the entire response must be a period '.'.

    Return:
    - (True, message) if valid
    - (False, detailed English guidance) if invalid
    """
    if not response or not response.strip():
        return (
            False,
            "The response is empty. Provide a final sentence and ensure the last non-whitespace character is a period '.'."
        )

    if _final_char_is_period(response):
        return (
            True,
            "Valid: The response ends with a period."
        )

    return (
        False,
        "The response must end with a period. Trim trailing spaces and ensure the final character is '.' (e.g., '... vehicle type.'). Do not place quotes, emojis, or extra characters after the period."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Identifiers constraint:
    - "The agent's response must include the exact phrase '[Answer]' immediately before
      the final sentence containing the banned vehicle type."

    Operational interpretation for validation:
    - The final sentence should start with the exact token '[Answer]' followed by a single
      space and then the content (i.e., the banned vehicle type statement).
    - We check that the last sentence (as parsed by ., !, ?) begins with '[Answer] '.

    Return:
    - (True, message) if valid
    - (False, detailed English guidance) if invalid
    """
    if not response or not response.strip():
        return (
            False,
            "The response is empty. Include a final sentence that begins with the exact token '[Answer]' followed by a space and then the banned vehicle type."
        )

    last_sentence = _last_nonempty_sentence(response)
    if not last_sentence:
        return (
            False,
            "Could not detect a final sentence. Provide a final sentence that starts with '[Answer] ' and ends with a period (e.g., '[Answer] Motorcycles.')."
        )

    # Check final sentence begins with [Answer] + space and then some content
    if ANSWER_LEADING_PATTERN.match(last_sentence):
        return (
            True,
            "Valid: The final sentence begins with the exact token '[Answer]' followed by content."
        )

    # Diagnose common issues for better guidance
    if "[Answer]" not in last_sentence:
        # Maybe [Answer] appears earlier in the response but not in the final sentence
        if "[Answer]" in response:
            return (
                False,
                "Place the exact token '[Answer]' at the very start of the final sentence. Example: '... prior content. [Answer] Motorcycles.' Ensure there is a space after '[Answer]' and the sentence ends with a period."
            )
        else:
            return (
                False,
                "Include the exact token '[Answer]' at the very beginning of the final sentence. Example: '[Answer] Motorcycles.' Use exactly '[Answer]' (case-sensitive, with brackets) followed by a single space."
            )

    # [Answer] is present in the final sentence, but not at the very beginning or spacing is wrong
    if last_sentence.lstrip().startswith("[Answer]") and not ANSWER_LEADING_PATTERN.match(last_sentence):
        return (
            False,
            "After '[Answer]' add exactly one space before the banned vehicle type. Example: '[Answer] Motorcycles.' Avoid colons or other characters immediately after the token."
        )

    return (
        False,
        "Move the exact token '[Answer]' to the very start of the final sentence and follow it with a single space, then the banned vehicle type, ending with a period. Example: '... [Answer] Motorcycles.'"
    )

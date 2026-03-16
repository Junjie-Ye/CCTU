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
 Your response must conclude with the identifier "**target temperature**" and end with a period to indicate the final result clearly. Your actions is constrained to a maximum of 6 tool calls in total, while the task execution must span at least 6 interaction turns and each tool must be called at most once.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "Your response must conclude with the identifier '**target temperature**' followed by a punctuation mark to indicate the final result clearly.")
- idx 4: ('Response', 'Punctuation', 'Ending punctuation (Specifies a period to ensure proper sentence closure.)')
"""

import re
import string
from typing import Tuple

# Shared helpers and constants

# Extend ASCII punctuation with common Unicode punctuation that may appear at the end of a response.
UNICODE_PUNCT_END = "...“”‘’‚‛‹›«»‐‐–—―·•、,。!?;:·《》〈〉【】[]()(){}[]「」『』’”"
TRAILING_PUNCT_CHARS = string.punctuation + UNICODE_PUNCT_END
TRAILING_PUNCT_AND_SPACE = TRAILING_PUNCT_CHARS + " \t\n\r"

# Some authors may wrap the identifier with quotes or emphasis; allow these wrappers at the very end.
WRAPPING_MARKS_END = "\"'`’”*)]>"

IDENTIFIER_PHRASE = "target temperature"
IDENTIFIER_PHRASE_LOWER = IDENTIFIER_PHRASE.lower()


def _rstrip_chars(text: str, chars: str) -> str:
    """Right-strip any combination of the provided characters."""
    return text.rstrip(chars)


def _strip_trailing_punct_and_space(text: str) -> str:
    """Remove trailing whitespace and punctuation commonly used at the end of sentences."""
    return _rstrip_chars(text, TRAILING_PUNCT_AND_SPACE)


def _strip_trailing_wrappers(text: str) -> str:
    """
    Remove common trailing wrapper marks (quotes, asterisks for bold/italic, closing brackets)
    that might appear immediately after the identifier.
    """
    # First remove trailing wrappers like quotes/brackets
    stripped = _rstrip_chars(text, WRAPPING_MARKS_END)
    # Then remove trailing emphasis markers like asterisks/underscores commonly used in Markdown
    stripped = _rstrip_chars(stripped, "*_")
    return stripped


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period ('.') as the final visible character.
    - Trims trailing whitespace before checking.
    """
    if response is None:
        return (
            False,
            "Response is None. Provide a non-empty string that ends with a period ('.').",
        )

    trimmed = response.rstrip()  # remove only whitespace on the right
    if not trimmed:
        return (
            False,
            "Response is empty after trimming whitespace. Add content that ends with a period ('.').",
        )

    last_char = trimmed[-1]
    if last_char == ".":
        return (
            True,
            "Valid: The response ends with a period as required.",
        )

    # Helpful diagnostics
    if last_char in TRAILING_PUNCT_CHARS:
        return (
            False,
            f"The final character is '{last_char}', but it must be a period ('.'). Replace the last character with a period so the response ends like: '... {IDENTIFIER_PHRASE}.'",
        )

    return (
        False,
        "The response does not end with a period. Ensure the last visible character is exactly '.' with no trailing spaces or other characters.",
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the identifier 'target temperature'
    immediately before the ending punctuation. Accepts optional trailing wrappers
    (quotes, asterisks) around the identifier, but the final words must be the
    exact phrase 'target temperature' (case-insensitive) at the very end before punctuation.
    """
    if response is None:
        return (
            False,
            "Response is None. Ensure the response concludes with the exact identifier 'target temperature' before the final punctuation.",
        )

    # Remove trailing whitespace and punctuation to examine the core ending words.
    core = _strip_trailing_punct_and_space(response)
    # Remove optional trailing wrapper characters like quotes or asterisks
    core = _strip_trailing_wrappers(core)

    core_lower = core.lower()

    # Quick pass condition: ends with the identifier phrase
    if core_lower.endswith(IDENTIFIER_PHRASE_LOWER):
        return (
            True,
            "Valid: The response ends with the identifier 'target temperature' before the final punctuation.",
        )

    # Build diagnostics about what the last two words are
    # Extract words using a simple pattern (letters plus optional internal apostrophes)
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", core_lower)
    if not words:
        return (
            False,
            "No terminal words detected at the end of the response. Ensure the very last words before punctuation are exactly 'target temperature', then add the final period.",
        )

    last_two = " ".join(words[-2:]) if len(words) >= 2 else words[-1]

    if IDENTIFIER_PHRASE_LOWER in response.lower():
        return (
            False,
            f"The response contains the identifier but does not place it at the very end. The last words are '{last_two}'. Move the exact phrase 'target temperature' to be the final words before punctuation, then end with a period: '... target temperature.'.",
        )

    # Not present at all
    return (
        False,
        f"The identifier 'target temperature' is missing at the end. Append the exact phrase 'target temperature' as the final words before punctuation, then end with a period. Example: '... {IDENTIFIER_PHRASE}.'.",
    )

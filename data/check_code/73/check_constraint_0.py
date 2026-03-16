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
 The answer must end with a period to ensure proper sentence closure. Additionally, each of the following tools used in the correct trajectory must be called at most once: conservation_award_winner_finder, nature_reserve_association_finder, species_locator, zoological_research_finder, individual_location_finder, festival_finder. The final response must be formatted using Markdown, with the festival name presented in bold text. The solution must be completed within 6 to 8 interaction turns to maintain efficiency while allowing for necessary adjustments. The response must contain between 10 and 50 characters (inclusive) to ensure conciseness and avoid unnecessary elaboration.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The response must end with a period to ensure proper sentence closure.')
- idx 2: ('Response', 'Format', 'The response must be formatted using Markdown, including at least one bold text element to highlight the festival name in the final answer.')
"""

import re
from typing import Tuple, List

# Helper: find all bold spans in Markdown (**text** or __text__)


def _find_bold_spans(response: str) -> List[str]:
    """
    Return the list of contents inside Markdown bold spans.
    Supports **bold** and __bold__.
    """
    # Non-greedy to capture smallest spans; allow any chars except newline greedily.
    star_spans = re.findall(r'\*\*(.+?)\*\*', response, flags=re.DOTALL)
    underscore_spans = re.findall(r'__(.+?)__', response, flags=re.DOTALL)
    return star_spans + underscore_spans

# Helper: determine if the last visible character (ignoring Markdown emphasis markers) is '.'


def _ends_with_visible_period(response: str) -> bool:
    """
    Returns True if, after ignoring trailing Markdown emphasis markers (* and _),
    the last visible character is a period '.'.
    Examples that pass:
      "**FestivalName.**"
      "__FestivalName.__"
      "**FestivalName.**  " (trailing whitespace)
    Examples that fail:
      "**FestivalName**" (no period)
      "**FestivalName**!" (ends with '!')
    """
    s = response.rstrip()
    # Remove any trailing emphasis markers (* or _) at the very end
    i = len(s) - 1
    while i >= 0 and s[i] in {'*', '_'}:
        i -= 1
    if i < 0:
        return False
    return s[i] == '.'

# Helper: check that at least one bold span has meaningful content (not empty/whitespace-only)


def _has_valid_bold_span(response: str) -> bool:
    spans = _find_bold_spans(response)
    for content in spans:
        # Content must contain at least one non-space character
        if content.strip():
            return True
    return False


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period as the last visible character.
    The check ignores trailing Markdown emphasis markers (** or __) and whitespace.
    """
    if _ends_with_visible_period(response):
        return (
            True,
            "Pass: The last visible character is a period. Keep the period as the final visible character (e.g., **FestivalName.**)."
        )
    # Provide actionable guidance
    return (
        False,
        "Fail: The response must end with a period as the last visible character. "
        "Append a single '.' at the end. If the festival name is bolded, place the period inside the bold span, "
        "immediately before the closing ** or __, for example: **FestivalName.**. "
        "Do not add any characters after the period (except the bold closing markers) and avoid extra trailing text."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response uses Markdown and includes at least one bold element
    to highlight the festival name (e.g., **FestivalName** or __FestivalName__).
    """
    # Check presence of at least one valid bold span
    if not _has_valid_bold_span(response):
        return (
            False,
            "Fail: No valid Markdown bold span was found. "
            "Wrap the festival name in bold using ** or __, for example: **FestivalName**. "
            "For this task, include the period inside the bold span so the rendered text ends with a dot, e.g., **FestivalName.**. "
            "Ensure the bold markers are balanced (exactly two leading and two trailing asterisks or underscores) "
            "and the bold content is not empty."
        )

    # Optional sanity: detect obviously unbalanced bold markers to give clearer guidance
    # This is a heuristic; it won't catch every edge case but helps common mistakes.
    if ('**' in response and len(re.findall(r'\*\*', response)) % 2 != 0) or \
       ('__' in response and len(re.findall(r'__', response)) % 2 != 0):
        return (
            False,
            "Fail: Unbalanced bold markers detected. "
            "Use matched pairs for bold: **bold** or __bold__. "
            "Ensure you do not leave an opening or closing marker without its pair. "
            "Example of a correct final answer: **FestivalName.**"
        )

    return (
        True,
        "Pass: Markdown formatting with at least one bold span is present. "
        "Keep the festival name in bold and ensure the period appears inside the bold span (e.g., **FestivalName.**)."
    )

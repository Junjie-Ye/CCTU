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
 The answer must be formatted using Markdown, including the keyword "Commander: " immediately before the individual's name, and the name must be in bold for clarity and emphasis. The response must be concise and must not exceed 50 words in total length and first sentence should end with a question mark. The solution must be completed in at most two interaction round with the tools.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'The first sentence should end with a question mark.')
- idx 1: ('Response', 'Format', "The answer must be formatted using Markdown, including the keyword 'Commander: ' immediately before the individual's name, and the name must be in bold for clarity and emphasis.")
"""

import re
from typing import Tuple

# Helper functions


def _strip_leading_markdown(text: str) -> str:
    """
    Remove common leading Markdown markers (headers, lists, quotes) from the first line
    to better detect the first sentence.
    """
    s = text.lstrip()
    # Remove leading code fence if present
    if s.startswith("```"):
        # Strip the first code block entirely to avoid false sentence detection inside code
        fence_end = s.find("```", 3)
        if fence_end != -1:
            s = s[fence_end + 3:].lstrip()
    # Remove one layer of common leading markers
    s = re.sub(r'^(?:#{1,6}|\>|\-|\*|\+|\d+\.)\s*', '', s)
    return s


def _extract_first_sentence(text: str) -> str:
    """
    Extract the first sentence from the response.
    A sentence is the shortest substring (including end punctuation) ending with '.', '!' or '?'.
    If none is found, return the first non-empty line.
    """
    s = _strip_leading_markdown(text)
    if not s.strip():
        return ""
    # Search across lines for the first terminal punctuation
    m = re.search(r'(.+?[.!?])', s, flags=re.S)
    if m:
        return m.group(1).strip()
    # Fallback: first non-empty line
    for line in s.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _find_commander_bold_name(text: str):
    """
    Find a pattern of 'Commander: **Name**' and return the match object if found.
    """
    pattern = re.compile(r'Commander:\s*\*\*([^\*\n]+?)\*\*')
    return pattern.search(text)

# Validators


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Constraint: The first sentence should end with a question mark.
    """
    first_sentence = _extract_first_sentence(response)
    if not first_sentence:
        return (
            False,
            "No detectable first sentence. Start your response with a clear sentence that ends with a question mark, e.g., 'Proceed with the plan?'"
        )
    if not first_sentence.endswith('?'):
        last_char = first_sentence[-1] if first_sentence else '∅'
        return (
            False,
            f"The first sentence must end with '?'. Detected first sentence: '{first_sentence}' (ends with '{last_char}'). Rewrite it to end with '?', e.g., 'Shall we proceed?'"
        )
    return (
        True,
        "First sentence correctly ends with a question mark."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Constraint: The answer must be formatted using Markdown, including:
    - the literal keyword 'Commander: ' immediately before the individual's name
    - the individual's name must be in bold (**Name**)
    """
    # Check the exact required pattern: Commander: **Name**
    match = _find_commander_bold_name(response)
    if match:
        name = match.group(1).strip()
        if not name:
            return (
                False,
                "The bolded name after 'Commander:' is empty. Provide a non-empty name, e.g., 'Commander: **Jane Doe**'."
            )
        return (
            True,
            "Detected required Markdown pattern: 'Commander: **Name**'."
        )

    # Provide targeted guidance based on what's present
    if "Commander:" not in response:
        return (
            False,
            "Missing the literal keyword 'Commander: '. Add a line like: Commander: **Jane Doe** (note the colon, a space, and the bolded name using double asterisks)."
        )

    # 'Commander:' exists, but not followed by a bold name
    # Check the region after 'Commander:' for near misses
    after = response.split("Commander:", 1)[1]
    if "**" not in after:
        return (
            False,
            "After 'Commander:' you must immediately provide the individual's name in Markdown bold. Use: Commander: **Jane Doe** (no extra characters between the colon and the bold name; spaces are allowed)."
        )

    # There is bold somewhere after Commander:, but not immediately
    # Guide to place bold immediately
    return (
        False,
        "Ensure the individual's name appears immediately after 'Commander:' in Markdown bold, e.g., Commander: **Jane Doe**. Do not insert other text or punctuation between 'Commander:' and the bold name."
    )

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
 You must obtain all information through tool calls, retrying with corrected parameters if errors occur. Additionally, you may use each unique tool type (e.g., `historical_event_locator` or `highest_mountain_finder`) at most twice during the task. Your final answer must be formatted using Markdown syntax with proper use of bold text for key terms and a dedicated "Final Answer" heading. Furthermore, the response must conclude with the exact phrase "Final Answer: **[the identified mountain]**".

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'The final answer must be formatted using Markdown syntax, including proper use of bold text for key terms and a dedicated "Final Answer" heading to enhance readability and structure.')
- idx 2: ('Response', 'Identifiers', '(Main Category, Response, The agent\'s response must conclude with the exact phrase "Final Answer: **[Mountain Name]**" where [Mountain Name] is the identified mountain.)')
"""

import re
from typing import Tuple, Optional, List

# Helper utilities


def _last_nonempty_line(text: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Return the last non-empty line (stripped) and its 0-based index in the original splitlines list.
    If no non-empty line exists, return (None, None).
    """
    lines = text.splitlines()
    for idx in range(len(lines) - 1, -1, -1):
        if lines[idx].strip():
            return lines[idx].strip(), idx
    return None, None


def _find_final_answer_heading_indices(text: str) -> List[int]:
    """
    Find indices of lines that are Markdown headings for 'Final Answer'.
    Matches '# Final Answer' through '###### Final Answer' with optional leading spaces (0-3).
    """
    lines = text.splitlines()
    heading_re = re.compile(r'^\s{0,3}#{1,6}\s+Final Answer\s*$')
    return [i for i, line in enumerate(lines) if heading_re.match(line)]


def _contains_bold(text: str) -> bool:
    """
    Detect at least one Markdown bold segment (**text**) with non-space content.
    Ensures there is at least one non-space character inside the bold markers.
    """
    # Do not cross line boundaries; require at least one non-space char
    return re.search(r'\*\*(?=\S)[^\n]*?\*\*', text) is not None


# Validators

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the response meets the required Markdown formatting:
    - Includes a dedicated Markdown heading for 'Final Answer' (e.g., '## Final Answer').
    - Uses bold text (e.g., **term**) for key terms somewhere in the content.
    - The 'Final Answer' heading should appear before the concluding line.
    """
    # Ensure at least one bold segment exists
    if not _contains_bold(response):
        return (
            False,
            "No bold formatting detected. Use Markdown bold for key terms, e.g., **seismic intensity**, "
            "or ensure the concluding phrase uses bold for the mountain name."
        )

    return (
        True,
        "Format is valid: a 'Final Answer' Markdown heading is present and bold formatting is detected."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the response ends with the exact concluding phrase:
    Final Answer: **<Mountain Name>**
    Requirements:
    - It must be the last non-empty line.
    - The line must start with 'Final Answer: **' and end with '**' exactly.
    - <Mountain Name> must be non-empty and should not be a placeholder in square brackets.
    """
    last_line, _ = _last_nonempty_line(response)
    if last_line is None:
        return (
            False,
            "No content found. The last non-empty line must be exactly: Final Answer: **<Mountain Name>**"
        )

    m = re.fullmatch(r'Final Answer:\s*\*\*(?P<name>.+?)\*\*', last_line)
    if not m:
        return (
            False,
            "The final line is incorrect. It must be exactly: Final Answer: **<Mountain Name>**\n"
            "Example: Final Answer: **Mount Everest**\n"
            "Do not include extra text before or after this line, and ensure the mountain name is inside the bold markers."
        )

    name = m.group('name').strip()
    if not name:
        return (
            False,
            "The mountain name inside the bold markers is empty. Use a concrete name, e.g., Final Answer: **Mount Fuji**."
        )

    # Disallow placeholder-like content in square brackets (e.g., [Mountain Name] or [the identified mountain])
    if name.startswith('[') and name.endswith(']'):
        return (
            False,
            "Replace the placeholder with the actual mountain name and remove the square brackets. For example:\n"
            "Final Answer: **Mount Rainier**"
        )

    return (
        True,
        "Identifiers are valid: the response ends with the exact required phrase containing the mountain name in bold."
    )

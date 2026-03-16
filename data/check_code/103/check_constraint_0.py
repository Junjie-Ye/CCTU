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
 Your response must include the final numerical answer enclosed within a LaTeX-style box using the format $\boxed{X}$, where X is the calculated value in million, must be between 10 and 50 words in length to ensure conciseness while providing necessary details, must end with a period to ensure proper sentence closure, and must contain a valid JSON object with key-value pairs, correct use of commas, colons, and quotation marks, and must be successfully parseable without errors.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'The final numerical answer must be enclosed within a LaTeX-style box using the format $\\boxed{X}$, where X is the calculated value in million.')
- idx 2: ('Response', 'Punctuation', 'Ending punctuation (The response must end with a period to ensure proper sentence closure.)')
- idx 3: ('Response', 'Format', '("Response", "Format", "JSON (The agent\'s entire response must contain a valid JSON object, adhering to proper syntax rules including key-value pairs, correct use of commas, colons, and quotation marks, and ensuring that the JSON can be successfully parsed without errors.)")')
"""

import json
import re
from typing import Tuple

# Helper regex to find LaTeX-style boxed numeric answer: $\boxed{X}$
BOXED_NUMBER_RE = re.compile(
    r'\$\s*\\boxed\{\s*([+-]?\d+(?:\.\d+)?)\s*\}\s*\$'
)


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a valid, parseable JSON object.
    - The response may contain other text besides the JSON.
    - The JSON must be syntactically valid (double quotes for strings, proper commas/colons).
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. The response must contain a valid JSON object."
        )

    # Try to find JSON object in the response
    json_str = None
    start_idx = -1

    # Look for JSON object pattern (starting with { and ending with })
    # We need to handle nested braces properly
    for i, char in enumerate(response):
        if char == '{':
            # Found potential start, try to extract the JSON
            start_idx = i
            brace_count = 0
            in_string = False
            escape_next = False
            json_candidate = []

            for j in range(start_idx, len(response)):
                ch = response[j]
                json_candidate.append(ch)

                if escape_next:
                    escape_next = False
                elif in_string:
                    if ch == '\\':
                        escape_next = True
                    elif ch == '"':
                        in_string = False
                else:
                    if ch == '"':
                        in_string = True
                    elif ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete JSON object
                            json_str = ''.join(json_candidate)
                            break

            if json_str:
                break

    if not json_str:
        # Alternative approach: try to find any substring that can be parsed as JSON
        # This is a simpler but less reliable approach
        for i in range(len(response)):
            for j in range(i + 1, len(response) + 1):
                substring = response[i:j]
                if substring.startswith('{') and substring.endswith('}'):
                    try:
                        parsed = json.loads(substring)
                        if isinstance(parsed, dict):
                            json_str = substring
                            break
                    except:
                        pass
            if json_str:
                break

    if not json_str:
        return (
            False,
            "No valid JSON object found in response. "
            "Include a JSON object (e.g., {\"difference_in_million\": \"...\"}) in your response."
        )

    # Validate the extracted JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        return (
            False,
            f"Invalid JSON found. JSON parse error: {e.msg}. "
            f"Ensure your JSON uses double quotes for strings, proper commas, and colons."
        )

    if not isinstance(parsed, dict):
        return (
            False,
            "The JSON object must be a dictionary (object). Found a different type. "
            "Return a JSON object like {\"difference_in_million\": \"...\"}."
        )

    return (
        True,
        f"Valid: Found a parseable JSON object in the response."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' as the last non-whitespace character.
    """
    trimmed = response.rstrip()
    if not trimmed:
        return (
            False,
            "Empty response. Provide the required content and ensure the final non-whitespace character is a period '.'."
        )
    if trimmed.endswith('.'):
        return (
            True,
            "Valid: The response ends with a period."
        )
    return (
        False,
        "The response must end with a period '.' as the last non-whitespace character. "
        "Add a final period at the end of the output."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the final numerical answer appears enclosed in a LaTeX-style box:
    $\boxed{X}$ where X is a number (in millions).
    - Requires exactly one occurrence of $\boxed{...}$.
    - X must be a valid number (integer or decimal, optional sign).
    """
    matches = BOXED_NUMBER_RE.findall(response)
    if len(matches) == 0:
        return (
            False,
            "Missing LaTeX-style boxed number. Include exactly one instance of the final numeric answer in the form "
            "$\\boxed{X}$, where X is the value in millions (e.g., $\\boxed{12.5}$)."
        )
    if len(matches) > 1:
        return (
            False,
            "Multiple boxed numbers found. Keep only one final boxed numeric answer of the form $\\boxed{X}$."
        )
    # Additional numeric sanity check is already ensured by the regex.
    return (
        True,
        "Valid: Exactly one LaTeX-style boxed numeric answer ($\\boxed{X}$) was found."
    )

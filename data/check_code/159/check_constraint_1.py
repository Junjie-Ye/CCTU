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
 You must use the specified tools to obtain all information and ensure your response contain a valid JSON object containing a "comparison" key with a boolean value and a "reasoning" key with a string. Additionally, if the agent intends to perform the operations related to identifying the valley and the mine, these must be executed simultaneously in a single action turn using the `natural_feature_locator` and `subterranean_mine_locator` tools, respectively. Usage of the `element_discovery_info` tool is conditional upon the prior execution of the `mineral_finder` tool. The total number of interaction turns must fall between 10 and 15, inclusive.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'Ending punctuation (Period)')
- idx 1: ('Response', 'Format', 'The agent\'s final answer must contain a valid JSON object containing a "comparison" key with a boolean value indicating the comparison result (true or false) and a "reasoning" key with a string value summarizing the reasoning behind the comparison.')
"""

import json
from typing import Tuple, List, Dict, Any


def _iter_json_objects(text: str) -> List[Dict[str, Any]]:
    """
    Scan the input text and return a list of parsed JSON objects (dicts).
    This function attempts to find balanced-brace substrings and parse them as JSON.
    It is tolerant of extra text before/after the JSON.
    """
    objs: List[Dict[str, Any]] = []
    n = len(text)
    i = 0
    while i < n:
        if text[i] == "{":
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                ch = text[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                candidate = text[i:j]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        objs.append(parsed)
                except Exception:
                    pass
                i = j
            else:
                # Unbalanced braces; stop scanning further.
                break
        else:
            i += 1
    return objs


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains a valid JSON object with:
    - "comparison": boolean (true/false in JSON)
    - "reasoning": non-empty string

    Returns:
        (bool, message)
        bool: True if valid JSON object with required keys is present.
        message: Detailed English guidance on how to fix issues if invalid.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Your final answer must include a valid JSON object. The response is empty or not a string. "
            "Include a JSON object with keys 'comparison' (boolean) and 'reasoning' (string). "
            "Example: {\"comparison\": false, \"reasoning\": \"The city area is X km^2, while the Moon's surface area is Y km^2.\"}"
        )

    objs = _iter_json_objects(response)
    if not objs:
        return (
            False,
            "No valid JSON object was found in your message. "
            "You must include a JSON object with keys 'comparison' (boolean) and 'reasoning' (string). "
            "Ensure you use strict JSON (double quotes, no trailing commas). "
            "Example: {\"comparison\": true, \"reasoning\": \"The city area (A km^2) exceeds the Moon's surface area (B km^2).\"}"
        )

    # Check each found JSON object; accept the first that satisfies the schema.
    for obj in objs:
        issues: List[str] = []

        if "comparison" not in obj:
            issues.append("Missing required key 'comparison'.")
        elif not isinstance(obj["comparison"], bool):
            issues.append(
                "Key 'comparison' must be a JSON boolean (true/false), not a string or number.")

        if "reasoning" not in obj:
            issues.append("Missing required key 'reasoning'.")
        else:
            if not isinstance(obj["reasoning"], str):
                issues.append("Key 'reasoning' must be a string.")
            elif not obj["reasoning"].strip():
                issues.append("Key 'reasoning' must be a non-empty string.")

        if not issues:
            return (
                True,
                "Valid format: A JSON object with 'comparison' (boolean) and 'reasoning' (string) is present."
            )

    # If we reach here, JSON objects were found but none met the schema.
    return (
        False,
        "A JSON object was found, but it does not meet the required schema. "
        "Fix the following: ensure it includes 'comparison' (boolean true/false) and 'reasoning' (non-empty string). "
        "Example of a valid object: {\"comparison\": false, \"reasoning\": \"The city area is smaller than the Moon's surface area.\"}"
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final message ends with a period '.' (ASCII dot) after trimming trailing whitespace.

    Returns:
        (bool, message)
        bool: True if the final non-whitespace character is a period.
        message: Detailed English guidance on how to fix issues if invalid.
    """
    if not isinstance(response, str) or not response:
        return (
            False,
            "Your final message must end with a period '.'. The response is empty or not a string. "
            "Add a concluding sentence or place a period at the very end of the message."
        )

    trimmed = response.rstrip()
    if trimmed.endswith("."):
        return (
            True,
            "Valid punctuation: the final non-whitespace character is a period '.'."
        )

    return (
        False,
        "Your final message must end with a single ASCII period '.'. "
        "If you output JSON, keep the JSON valid and place the period after the closing brace, "
        "or add a short concluding sentence after the JSON that ends with a period. "
        "Do not add any characters after the final period."
    )

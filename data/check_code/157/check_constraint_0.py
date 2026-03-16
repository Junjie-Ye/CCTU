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
Rank these values from greatest to least: (a) the volume of water in cubic meters in the waterfall near the location of the writer who crafted the acclaimed novel set in Japan, (b) the number of languages spoken by the diplomat who opened trade routes, and (c) the length of the historic road in kilometers, paved by the emperor leading a major dynasty. If the agent intends to invoke the `historical_road_length_calculator`, the `historical_leader_infrastructure_finder` must strictly be executed beforehand. You may call the `literary_search_tool` at most 2 times. Your final answer must contain a valid JSON object, including a JSON key-value structure for each ranked item, with the keys 'a', 'b', and 'c' corresponding to the three values. The JSON must be syntactically valid and should be enclosed in curly braces. Your final answer must also end with a period to ensure proper sentence closure and must not exceed 200 characters in length.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', '(Main Category, Punctuation, Ending punctuation (The final response must end with a period to ensure proper sentence closure.))')
- idx 2: ('Response', 'Format', "The answer must contain a valid JSON object, including a JSON key-value structure for each ranked item, with the keys 'a', 'b', and 'c' corresponding to the three values. The JSON must be syntactically valid and should be enclosed in curly braces.")
"""

import json
from typing import Tuple

# Helper function: safely strip a single trailing period and surrounding whitespace


def _strip_trailing_period(s: str) -> Tuple[str, bool]:
    trimmed = s.rstrip()
    if trimmed.endswith('.'):
        return trimmed[:-1].rstrip(), True
    return trimmed, False


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The content (ignoring a single trailing period) is a syntactically valid JSON object.
    - The JSON object is enclosed in curly braces and contains exactly keys 'a', 'b', and 'c'.
    """
    s = response.strip()

    json_candidate, _had_period = _strip_trailing_period(s)

    if not json_candidate.startswith('{') or not json_candidate.endswith('}'):
        return (
            False,
            "Place a valid JSON object strictly between '{' and '}', with no extra text outside. "
            "Append a single period '.' immediately after the closing brace."
        )

    try:
        obj = json.loads(json_candidate)
    except json.JSONDecodeError as e:
        return (
            False,
            f"Invalid JSON syntax: {e}. Ensure proper quoting of keys/strings and commas. "
            "Use exactly one JSON object followed by a single period."
        )

    if not isinstance(obj, dict):
        return (
            False,
            "The content must be a JSON object (e.g., {\"a\":..., \"b\":..., \"c\":...}), not an array or other type."
        )

    required_keys = {'a', 'b', 'c'}
    keys = set(obj.keys())
    missing = required_keys - keys
    extra = keys - required_keys

    if missing:
        return (
            False,
            f"Missing required keys: {', '.join(sorted(missing))}. Include exactly the keys 'a','b','c'."
        )
    if extra:
        return (
            False,
            f"Remove extra keys: {', '.join(sorted(extra))}. Keep only 'a','b','c' in the JSON object."
        )

    return (
        True,
        "Format is valid: a single JSON object with keys 'a','b','c'. Ensure values clearly encode the rank order. "
        "Keep the total length ≤ 200 characters."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final character of the response is a period.
    """
    s = response.rstrip()
    if s.endswith('.'):
        return True, "Ending punctuation is correct: the response ends with a single period."
    return (
        False,
        "Append a single period '.' as the final character of the response, placed immediately after the closing '}'. "
        "Do not add any text after the period."
    )

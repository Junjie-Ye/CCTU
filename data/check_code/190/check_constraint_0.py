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
Rank these from highest to lowest: (a) the height of the largest waterfall visited by the artist who painted the famous mural in the city park, (b) the capacity of the theater in the city where the poet who wrote the sonnet named after a celestial body resides, and (c) the number of islands in the largest lake in the world. Your final answer must be formatted as a valid JSON object that includes the three ranked values, their corresponding numerical results, and a clear ranking order from highest to lowest. You must ensure that each tool is called at most 3 times during the process. If the agent intends to utilize either `historical_visit_locator` or `landmark_info_retriever`, it is strictly required to ensure that `artist_information_retriever` has been executed beforehand. The total number of tool calls must be between 8 and 10.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The agent must provide the final answer as a valid JSON object that includes the three ranked values, their corresponding numerical results, and a clear ranking order from highest to lowest.')
"""

import json
import math
from typing import Tuple, Any, List, Dict


def _is_number(value: Any) -> bool:
    """
    Check if value is a real finite number (int or float), excluding booleans and NaN/Infinity.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    return False


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is:
    - A bare, valid JSON object (no code fences or extra prose).
    - Contains keys "ranking" (list of exactly 3 unique strings) and "values" (object).
    - Each item in ranking exists as a key in "values".
    - Each corresponding value is a real finite number (int or float; not string, bool, NaN, or Infinity).
    - The ranking list is ordered from highest to lowest according to the numeric values (non-increasing).

    Returns:
        (bool, str): A tuple where bool indicates validity and str provides detailed guidance in English.
    """
    s = response.strip()
    # 1) Must be bare JSON (no code fences or extra text).
    if s.startswith("```") or s.endswith("```"):
        return (
            False,
            "The response must be a bare JSON object without code fences. Remove ``` and output only the JSON object."
        )

    # 2) Parse JSON
    try:
        obj = json.loads(s)
    except Exception as e:
        return (
            False,
            "The response is not valid JSON or includes extra text. Output only a single JSON object, e.g.: "
            '{"ranking":["waterfall_height","theater_capacity","island_count"],'
            '"values":{"waterfall_height":720,"theater_capacity":2500,"island_count":11450}}. '
            f"JSON parsing error: {e}"
        )

    # 3) Top-level must be an object
    if not isinstance(obj, dict):
        return (
            False,
            "The top-level JSON must be an object (dictionary), not an array, string, or number."
        )

    # 4) Required keys
    missing_keys = [k for k in ("ranking", "values") if k not in obj]
    if missing_keys:
        return (
            False,
            f"Missing required key(s): {missing_keys}. Include both 'ranking' (list) and 'values' (object)."
        )

    ranking = obj["ranking"]
    values = obj["values"]

    # 5) ranking must be a list of exactly 3 unique strings
    if not isinstance(ranking, list):
        return (
            False,
            "The 'ranking' field must be a list of exactly three strings representing the ranked items."
        )
    if len(ranking) != 3:
        return (
            False,
            f"The 'ranking' list must contain exactly 3 items; found {len(ranking)}."
        )
    if not all(isinstance(x, str) for x in ranking):
        return (
            False,
            "All entries in 'ranking' must be strings (e.g., 'waterfall_height', 'theater_capacity', 'island_count')."
        )
    if len(set(ranking)) != 3:
        return (
            False,
            "The 'ranking' list must contain three unique entries; duplicates detected."
        )

    # 6) values must be an object with numeric values for each ranking key
    if not isinstance(values, dict):
        return (
            False,
            "The 'values' field must be a JSON object mapping each ranked key to a numeric result."
        )

    missing_value_keys = [k for k in ranking if k not in values]
    if missing_value_keys:
        return (
            False,
            f"The 'values' object must include numeric entries for all ranked keys; missing: {missing_value_keys}."
        )

    non_numeric_keys = [k for k in ranking if not _is_number(values[k])]
    if non_numeric_keys:
        return (
            False,
            "Each ranked key in 'values' must map to a real, finite number (int or float). "
            f"The following keys are non-numeric, boolean, NaN, or Infinity: {non_numeric_keys}. "
            "Use numeric literals (e.g., 123 or 123.45), not strings."
        )

    # 7) Verify ordering: highest to lowest (non-increasing)
    vals = [float(values[k]) for k in ranking]
    order_violations = []
    for i in range(len(vals) - 1):
        if vals[i] < vals[i + 1]:
            order_violations.append(
                (ranking[i], values[ranking[i]], ranking[i + 1], values[ranking[i + 1]]))

    if order_violations:
        corrected = sorted(
            ranking, key=lambda k: float(values[k]), reverse=True)
        return (
            False,
            "The 'ranking' list must be ordered from highest to lowest according to the numeric 'values'. "
            "Detected out-of-order pairs: "
            + "; ".join(
                f"'{a}' ({av}) < '{b}' ({bv})"
                for a, av, b, bv in order_violations
            )
            + f". Suggested 'ranking': {corrected}."
        )

    # Success
    return (
        True,
        "Valid format: JSON object with 'ranking' (3 unique items) and 'values' (numeric results), ordered highest to lowest. "
        "Optional tip: Use canonical keys like 'waterfall_height', 'theater_capacity', and 'island_count' for clarity."
    )

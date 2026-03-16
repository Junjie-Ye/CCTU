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
 Your answer must be at least 50 words and clearly explain the numerical comparison between the artifact’s price and the theater’s capacity. Additionally, if the agent intends to use the `historical_affiliation_finder` tool, it is strictly required to ensure that `historian_finder` has been invoked beforehand. The `astronomical_historian` tool can only be legitimately invoked if the `historical_affiliation_finder` tool has already been executed within the trajectory. The final answer must be structured as a valid JSON object with keys 'comparison' and 'result', where 'comparison' contains the numerical values and 'result' states whether the price exceeds the capacity.

response_constraints_non_length:
- idx 2: ('Response', 'Format', "(Response, Format, The answer must be structured as a valid JSON object with keys 'comparison' and 'result', where 'comparison' contains the numerical values and 'result' states whether the price exceeds the capacity.)")
"""

import json
import re
from typing import Any, Dict, List, Tuple, Union

# -------- Helper utilities --------

CODE_FENCE_RE = re.compile(
    r'^\s*`{3,}\s*(?:json)?\s*\n(.*?)\n`{3,}\s*$', re.DOTALL | re.IGNORECASE
)

NUMBER_RE = re.compile(r'[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?')


def _strip_code_fences(text: str) -> str:
    """
    Remove Markdown code fences to recover raw JSON content.
    """
    m = CODE_FENCE_RE.match(text)
    return m.group(1).strip() if m else text.strip()


def _collect_numbers(obj: Any, acc: List[float]) -> None:
    """
    Recursively collect numeric values from a Python object (parsed JSON).
    Accepts:
      - ints/floats directly
      - strings that contain numeric tokens
      - nested dicts/lists
    Numbers with thousands separators are normalized.
    """
    if isinstance(obj, (int, float)):
        acc.append(float(obj))
    elif isinstance(obj, str):
        # Extract numeric tokens from string
        for tok in NUMBER_RE.findall(obj):
            # Normalize thousands separators like "12,345.67"
            normalized = tok.replace(",", "")
            try:
                acc.append(float(normalized))
            except ValueError:
                continue
    elif isinstance(obj, list):
        for v in obj:
            _collect_numbers(v, acc)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_numbers(v, acc)
    # Ignore other types


def _result_is_clear(result_value: Any) -> bool:
    """
    Determine if 'result' clearly states whether price exceeds capacity.
    Accept if:
      - Boolean True/False
      - A string that unambiguously indicates exceedance or non-exceedance.
    """
    if isinstance(result_value, bool):
        return True
    if isinstance(result_value, str):
        s = result_value.strip().lower()
        # Clear positive indications
        positive_patterns = [
            "exceeds", "is greater than", ">", "more than"
        ]
        # Clear negative or non-exceed indications
        negative_patterns = [
            "does not exceed", "doesn't exceed", "is less than", "<", "not exceed", "≤", "equal", "equals", "is equal to", "same as"
        ]

        pos = any(p in s for p in positive_patterns)
        neg = any(n in s for n in negative_patterns)

        # Accept if one side is clearly indicated and not contradicted
        if pos and not neg:
            return True
        if neg and not pos:
            return True
    return False


def _format_extra_keys_message(obj_keys: List[str]) -> str:
    return (
        "Only 'comparison' and 'result' are required. Extra keys were found: "
        f"{', '.join(k for k in obj_keys if k not in {'comparison', 'result'})}. "
        "Remove unrelated keys to strictly follow the required format."
    )

# -------- Validator for the 'format' response constraint --------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is:
      - A valid JSON object (no extra prose), optionally wrapped in Markdown fences
      - Contains keys 'comparison' and 'result'
      - 'comparison' contains the numerical values (at least two numbers are present)
      - 'result' clearly states whether price exceeds capacity (boolean or clear textual statement)

    Returns:
      (is_valid, message)
      - If invalid, message provides precise, actionable guidance in English.
      - If valid, message confirms success and gives optional improvement hints.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "Invalid: The response is empty or not a string. Return a JSON object only, e.g. "
            '{"comparison": "Artifact price 120000 vs theater capacity 950", "result": true}.'
        )

    raw = _strip_code_fences(response)

    # Try parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return (
            False,
            f"Invalid: The response is not valid JSON ({str(e)}). "
            "Return JSON only (no extra prose). Example: "
            '{"comparison": "Artifact price 120000 vs theater capacity 950", "result": false}.'
        )

    # Must be a JSON object
    if not isinstance(data, dict):
        return (
            False,
            "Invalid: The top-level JSON must be an object with keys 'comparison' and 'result'. "
            "Do not return an array or other types."
        )

    keys = set(data.keys())
    required = {"comparison", "result"}
    missing = required - keys
    if missing:
        return (
            False,
            "Invalid: Missing required key(s): "
            + ", ".join(sorted(missing))
            + ". Provide exactly 'comparison' (with the numerical values) and 'result' "
              "(stating whether price exceeds capacity)."
        )

    # Validate 'comparison'
    comparison = data.get("comparison")
    nums: List[float] = []
    _collect_numbers(comparison, nums)

    if len(nums) < 2:
        return (
            False,
            "Invalid: The 'comparison' field must include the numerical values for both the artifact's price "
            "and the theater's seating capacity. Provide at least two numeric values (e.g., 120000 and 950). "
            "You may place them in a string or a structured object."
        )

    # Validate 'result'
    result_value = data.get("result")
    if not _result_is_clear(result_value):
        return (
            False,
            "Invalid: The 'result' field must clearly state whether the price exceeds the capacity. "
            "Use a boolean (true if price > capacity, false otherwise) or a clear phrase such as "
            "'exceeds' or 'does not exceed'."
        )

    # Optional hint about extra keys
    extra_keys = [k for k in keys if k not in required]
    if extra_keys:
        return (
            True,
            "Valid: The JSON structure meets the required format. "
            + _format_extra_keys_message(list(keys))
        )

    return (
        True,
        "Valid: The response is a proper JSON object with 'comparison' containing numeric values and "
        "'result' clearly indicating exceedance."
    )

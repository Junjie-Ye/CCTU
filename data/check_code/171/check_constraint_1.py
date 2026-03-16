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
 Your answer must contain a valid JSON object with the following structure: {"result": "<comparison_result>", "museum_capacity": <number>, "city_population": <number>}. The comparison_result must be either "Yes" or "No", both numerical values must be integers representing the exact numbers retrieved from the tools, the response must conclude with the exact string 'END' to indicate completion, the population_data_retriever tool may be used no more than 3 times during the solution process, and the solution must be completed within 10 interaction turns.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must contain a valid JSON object with the specified structure: {"result": "<comparison_result>", "museum_capacity": <number>, "city_population": <number>}.')
- idx 1: ('Response', 'Identifiers', '(Response, End identifier, "The answer must conclude with the exact string \'END\' to indicate completion.")')
"""

import json
from typing import Tuple, List, Optional


def _extract_json_objects(text: str) -> List[dict]:
    """
    Scan the text and extract all top-level JSON objects by matching balanced braces.
    Handles braces inside quoted strings and escape sequences.
    Returns a list of successfully parsed dict objects (only dicts are kept).
    """
    objs: List[dict] = []
    in_string = False
    escape = False
    depth = 0
    start_idx: Optional[int] = None

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                if depth == 0:
                    start_idx = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start_idx is not None:
                        candidate = text[start_idx:i + 1]
                        try:
                            parsed = json.loads(candidate)
                            if isinstance(parsed, dict):
                                objs.append(parsed)
                        except Exception:
                            pass
                        start_idx = None
    return objs


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates the 'format' response constraint:
    - The answer must contain a valid JSON object with the exact structure:
      {"result": "<comparison_result>", "museum_capacity": <number>, "city_population": <number>}.
    - result must be the string "Yes" or "No" (case-sensitive).
    - museum_capacity and city_population must be integers (JSON numbers without quotes or decimals).
    - No extra keys are allowed; all three required keys must be present.
    """
    objs = _extract_json_objects(response)
    if not objs:
        return (
            False,
            "No valid JSON object was found. Provide exactly one top-level JSON object with keys "
            'result, museum_capacity, city_population (no extras). Example:\n'
            '{"result": "Yes", "museum_capacity": 123, "city_population": 456}\n'
            "Place the JSON object before the terminal END marker."
        )

    obj = objs[-1]  # Use the last JSON object found in the response

    expected_keys = {"result", "museum_capacity", "city_population"}
    obj_keys = set(obj.keys())

    missing = expected_keys - obj_keys
    if missing:
        return (
            False,
            f"Missing required key(s): {', '.join(sorted(missing))}. "
            "Include all of: result, museum_capacity, city_population (spelled exactly)."
        )

    extra = obj_keys - expected_keys
    if extra:
        return (
            False,
            f"Unexpected extra key(s): {', '.join(sorted(extra))}. "
            "Remove them so the object has exactly: result, museum_capacity, city_population."
        )

    # Validate 'result'
    result_val = obj.get("result")
    if not isinstance(result_val, str):
        return (
            False,
            'The "result" field must be a string with value "Yes" or "No". '
            "Do not use booleans or other types."
        )
    if result_val not in {"Yes", "No"}:
        return (
            False,
            'The "result" field must be exactly "Yes" or "No" (case-sensitive). '
            f'Current value: {result_val!r}.'
        )

    # Validate integers for museum_capacity and city_population
    def _is_int_like(value) -> bool:
        # Ensure it's an actual int (bool is a subclass of int, so exclude bool).
        return isinstance(value, int) and not isinstance(value, bool)

    mc_val = obj.get("museum_capacity")
    if not _is_int_like(mc_val):
        val_type = type(mc_val).__name__
        return (
            False,
            'The "museum_capacity" field must be an integer JSON number (no quotes, no decimals). '
            f"Current type/value: {val_type}/{mc_val!r}. Example: \"museum_capacity\": 123"
        )

    cp_val = obj.get("city_population")
    if not _is_int_like(cp_val):
        val_type = type(cp_val).__name__
        return (
            False,
            'The "city_population" field must be an integer JSON number (no quotes, no decimals). '
            f"Current type/value: {val_type}/{cp_val!r}. Example: \"city_population\": 456"
        )

    return (
        True,
        "Valid: A JSON object with exactly the required keys and correct value types is present."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'identifiers' response constraint:
    - The answer must conclude with the exact string 'END' to indicate completion.
    - Only whitespace may follow END (none is preferred); no quotes or punctuation after END.
    """
    trimmed = response.rstrip()
    if not trimmed.endswith("END"):
        return (
            False,
            "The response must end with the exact token END. Append a newline (optional) and END as "
            "the final characters, with no quotes or punctuation after it. Example:\n"
            '{"result": "Yes", "museum_capacity": 123, "city_population": 456}\nEND'
        )
    return (
        True,
        "Valid: The response ends with the exact identifier END."
    )

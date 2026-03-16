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
 You must ensure that at least one interaction turn during the entire task involves the agent invoking at least 2 unique tool types simultaneously. Additionally, the agent is limited to invoking the 'musical_composition_finder' tool at most 2 times during the entire task. The agent's final answer must end with the phrase "Final Answer" followed by the numerical result enclosed in a box, like "Final Answer: $\boxed{<result>}$". The final answer must be concise and not exceed 500 characters. Furthermore, the final answer must contain a valid JSON object, including a "result" key with the numerical value as the product of the library's area and the year of the philosopher's first significant work.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', '(Main Category, Subcategory, "The agent\'s final answer must end with the phrase \'Final Answer\' followed by the numerical result enclosed in a box, like \'Final Answer: $\\\\boxed{<result>}$\'.")')
- idx 4: ('Response', 'Format', '(Response, Format, The final answer must contain a valid JSON object, including a "result" key with the numerical value as the product of the library\'s area and the year of the philosopher\'s first significant work)')
"""

import re
import json
from typing import Tuple, Optional, List
from decimal import Decimal, InvalidOperation

# Helper: try to parse a textual number to Decimal (supports commas, spaces, and scientific notation)


def _to_decimal_number(text: str) -> Optional[Decimal]:
    s = text.strip().replace(",", "").replace(" ", "")
    if not s:
        return None
    # Accept optional sign, digits, optional decimal, optional exponent
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", s):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None

# Helper: numeric equality with tolerance for non-integer values


def _decimal_equal(a: Decimal, b: Decimal, eps: Decimal = Decimal("1e-9")) -> bool:
    return abs(a - b) <= eps

# Helper: extract the final boxed number at the end of the response
# Must match: "Final Answer: $\boxed{<result>}$" at the end (ignoring trailing whitespace)


def _extract_final_boxed_number(response: str) -> Optional[Decimal]:
    pattern = re.compile(
        r"Final Answer:\s*\$\s*\\boxed\{\s*([^\}]+?)\s*\}\s*\$\s*$",
        re.DOTALL
    )
    m = pattern.search(response.strip())
    if not m:
        return None
    value_text = m.group(1)
    return _to_decimal_number(value_text)

# Helper: detect if a boxed clause exists but not at the end


def _exists_boxed_clause_anywhere(response: str) -> bool:
    return re.search(r"Final Answer:\s*\$\s*\\boxed\{.*?\}\s*\$", response, re.DOTALL) is not None

# Helper: find JSON objects within text by scanning brace pairs and validating via json.loads


def _find_json_objects(text: str) -> List[dict]:
    objs = []
    n = len(text)
    starts = [i for i, ch in enumerate(text) if ch == '{']
    for s in starts:
        # Iterate over possible closing positions
        for e in range(s + 1, n):
            if text[e] == '}':
                candidate = text[s:e + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        objs.append(parsed)
                except Exception:
                    pass
    return objs


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validates the 'identifiers' constraint:
    - The response must end with: Final Answer: $\boxed{<result>}$ where <result> is a pure number.
    """
    boxed_value = _extract_final_boxed_number(response)
    if boxed_value is None:
        # If exists anywhere but not at end, give a targeted message
        if _exists_boxed_clause_anywhere(response):
            return (
                False,
                "Move the clause 'Final Answer: $\\boxed{<number>}$' to the very end of the response, "
                "with no trailing text after it. Ensure the number inside \\boxed{ } is numeric only (no units or words)."
            )
        else:
            return (
                False,
                "End the response with: 'Final Answer: $\\boxed{<number>}$'. "
                "Use the exact phrase 'Final Answer:' followed by a TeX boxed numeric value. "
                "Example: Final Answer: $\\boxed{123456}$"
            )
    # If present, ensure it's purely numeric (already checked by parser)
    return (
        True,
        "Identifiers constraint satisfied: Response ends with 'Final Answer: $\\boxed{<number>}$' and the boxed value is numeric."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates the 'format' constraint:
    - The final answer must contain a valid JSON object.
    - The JSON must include a 'result' key with a numeric value.
    - The numeric JSON 'result' must match the number in the final boxed clause.
    - The response must not exceed 500 characters.
    """
    # Character limit check
    if len(response) > 500:
        return (
            False,
            "The final answer must be concise and not exceed 500 characters. "
            "Reduce content so the entire response is <= 500 characters, while still including the JSON object and the final boxed clause."
        )

    json_objs = _find_json_objects(response)
    if not json_objs:
        return (
            False,
            "Include a valid JSON object in the response. At minimum, provide: {\"result\": <number>} "
            "Place the JSON object in the message (e.g., before the final boxed clause)."
        )

    # Use the last detected JSON object
    json_obj = json_objs[-1]
    if "result" not in json_obj:
        return (
            False,
            "Your JSON object must contain a 'result' key with the numerical product value. "
            "Example: {\"result\": 123456}"
        )

    result_val = json_obj["result"]
    # Ensure result is numeric (int or float)
    if not isinstance(result_val, (int, float)):
        return (
            False,
            "The 'result' value in JSON must be numeric (int or float). "
            "Do not use strings: write {\"result\": 123456} not {\"result\": \"123456\"}."
        )

    # Ensure boxed clause exists and matches
    boxed_value = _extract_final_boxed_number(response)
    if boxed_value is None:
        return (
            False,
            "Add the closing clause 'Final Answer: $\\boxed{<number>}$' at the very end of the response. "
            "Its number must equal the JSON 'result' value."
        )

    try:
        result_decimal = Decimal(str(result_val))
    except InvalidOperation:
        return (
            False,
            "The 'result' value in JSON must be a plain number (int or float). "
            "Avoid non-numeric formats or special values."
        )

    if not _decimal_equal(boxed_value, result_decimal):
        return (
            False,
            f"The JSON 'result' ({result_decimal}) must exactly match the number inside the final $\\boxed{{ }}$ ({boxed_value}). "
            "Update either the JSON 'result' or the boxed number so they are identical."
        )

    # Cannot verify the actual product inputs, but remind the author
    return (
        True,
        "Format constraint satisfied: A valid JSON object with numeric 'result' is present, "
        "the response is <= 500 characters, and the boxed number matches the JSON 'result'. "
        "Ensure the 'result' truly equals the product of the library's area and the philosopher's year."
    )

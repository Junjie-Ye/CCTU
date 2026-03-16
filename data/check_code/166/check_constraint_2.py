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
 The solution must use between 8 and 12 total tool calls across all interaction steps to ensure thorough investigation while avoiding excessive redundancy. The total number of interaction turns must be at most 15. The final answer must contain a valid JSON object with a key 'answer' containing either 'Yes.' or 'No.' as its value, and the final answer must end with 'END' and no punctuation. The JSON must not include any additional keys or metadata beyond the required 'answer' key.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Main Category, Subcategory, Specific Constraint) = ("Response", "End identifier", "The final answer must end with \'END\' without any additional text.")')
- idx 2: ('Response', 'Format', "The final answer must contain a valid JSON object with a key 'answer' containing either 'Yes.' or 'No.' as its value. The JSON must not include any additional keys or metadata beyond the required 'answer' key.")
- idx 4: ('Response', 'Punctuation', '(Main Category, Subcategory, "The final answer must end with no punctuation")')
"""

import json
import unicodedata
from typing import List, Tuple, Optional


def _find_json_objects(text: str) -> List[Tuple[str, int, int]]:
    """
    Scan the text and return a list of tuples: (json_string, start_idx, end_idx),
    extracting top-level balanced JSON objects while respecting quoted strings.
    """
    objs: List[Tuple[str, int, int]] = []
    depth = 0
    start: Optional[int] = None
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            # ignore braces inside strings
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        objs.append((text[start: i + 1], start, i + 1))
                        start = None
    return objs


def _is_punctuation(char: str) -> bool:
    """
    Return True if the character is a Unicode punctuation character.
    """
    if not char:
        return False
    return unicodedata.category(char).startswith("P")


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Format constraint:
    - The final answer must contain a valid JSON object.
    - The object must have exactly one key: 'answer'.
    - 'answer' must be either 'Yes.' or 'No.' (including the period).
    - The JSON must not include any additional keys or metadata.
    Notes:
    - This validator focuses only on the JSON structure/content.
    - The 'END' marker and trailing punctuation are validated by other functions.
    """
    candidates = _find_json_objects(response)
    if not candidates:
        return (
            False,
            "No JSON object found. Include exactly one JSON object like: "
            '{"answer":"Yes."} or {"answer":"No."}. Place it before the END marker.'
        )

    valid_objs = []
    last_error_detail = None

    for obj_str, _, _ in candidates:
        try:
            parsed = json.loads(obj_str)
        except json.JSONDecodeError as e:
            last_error_detail = f"Invalid JSON syntax: {e}"
            continue
        if not isinstance(parsed, dict):
            last_error_detail = "The parsed JSON is not an object; it must be a single JSON object."
            continue
        keys = list(parsed.keys())
        if set(keys) != {"answer"} or len(keys) != 1:
            extra = [k for k in keys if k != "answer"]
            missing = [] if "answer" in parsed else ["answer"]
            detail_parts = []
            if extra:
                detail_parts.append(f"extra keys present: {extra}")
            if missing:
                detail_parts.append(f"missing required key: {missing}")
            last_error_detail = "JSON object must contain exactly one key 'answer'; " + \
                "; ".join(detail_parts)
            continue
        val = parsed["answer"]
        if not isinstance(val, str):
            last_error_detail = "The value of 'answer' must be a string: either 'Yes.' or 'No.'."
            continue
        if val not in ("Yes.", "No."):
            last_error_detail = "The 'answer' value must be exactly 'Yes.' or 'No.' (including the period)."
            continue
        # This candidate is valid
        valid_objs.append(parsed)

    if not valid_objs:
        return (
            False,
            last_error_detail
            or "A JSON object was found but invalid. Use exactly one object with only the 'answer' key, "
               "and set its value to 'Yes.' or 'No.'."
        )

    if len(valid_objs) > 1:
        return (
            False,
            "Multiple JSON objects detected. Provide exactly one JSON object with only the 'answer' key, "
            "then place the END marker on a new line."
        )

    return (
        True,
        "Valid: exactly one JSON object found with only the 'answer' key set to 'Yes.' or 'No.'."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Punctuation constraint:
    - The final answer must end with no punctuation.
    This validator inspects the last non-whitespace character.
    """
    # Identify the last non-whitespace character
    i = len(response) - 1
    while i >= 0 and response[i].isspace():
        i -= 1
    if i < 0:
        return (
            False,
            "The response is empty or whitespace-only. Provide the JSON object and end the response with END without punctuation."
        )
    last_char = response[i]
    if _is_punctuation(last_char):
        return (
            False,
            "The final character is punctuation. Ensure the response ends without punctuation; "
            "finish exactly with END as the last three characters and no trailing spaces."
        )
    return (
        True,
        "Valid: the response ends with a non-punctuation character."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    End identifier constraint:
    - The final answer must end with 'END' without any additional text.
    - No trailing whitespace or characters are allowed after END.
    """
    if not response.endswith("END"):
        # Check for common near-misses to provide targeted guidance
        trimmed = response.rstrip()
        if trimmed.endswith("END"):
            return (
                False,
                "Remove any trailing whitespace after END. The response must terminate exactly with END (no spaces or newline after it)."
            )
        if "END" in response:
            return (
                False,
                "Ensure END is the final three characters of the entire response with no text or whitespace after it."
            )
        return (
            False,
            "Append END at the very end of the response with no trailing spaces or punctuation. "
            "Place the JSON object first, then END on a new line."
        )
    return (
        True,
        "Valid: the response ends exactly with END and no trailing characters."
    )

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
 Your final answer must contain a valid JSON object with keys "landmark_age" and "mountain_height" containing their respective values, and a key "comparison_result" indicating whether the landmark's age is greater than the mountain's height (true or false). The solution must be derived using no more than 12 total tool calls across all interaction turns. The final response must end with a period to ensure proper sentence closure. The JSON response must use double colons (::) as a delimiter between key-value pairs to ensure clear separation. The response must be between 50 and 150 characters long, ensuring it is concise yet includes all required information. Additionally, the agent must invoke between 2 and 4 unique tool types in at least one interaction turn during the task to ensure efficient parallelism while preventing excessive complexity. Each tool can be used at most 3 times to ensure efficient resource usage and prevent over-reliance on a single tool.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The final answer must contain a valid JSON object with keys "landmark_age" and "mountain_height" containing their respective values, and a key "comparison_result" indicating whether the landmark\'s age is greater than the mountain\'s height (true or false) with double colons (::) as a delimiter.')
- idx 2: ('Response', 'Punctuation', 'The final response must end with a period to ensure proper sentence closure.')
- idx 3: ('Response', 'Identifiers', 'Delimiting identifier (The JSON response must use double colons (::) as a delimiter between key-value pairs to ensure clear separation.)')
"""

import re
import json
from typing import Tuple, Optional, Any

# ----------------------------
# Helper utilities (shared)
# ----------------------------


def _strip_trailing_period(response: str) -> Tuple[str, bool]:
    """
    Remove one trailing period if present (ignoring trailing whitespace).
    Returns (text_without_final_period, had_period).
    """
    s = response.rstrip()
    if s.endswith('.'):
        return s[:-1].rstrip(), True
    return s, False


def _extract_core_json_text(response: str) -> Tuple[Optional[str], str]:
    """
    Extract the core JSON-like object text from the response.
    The response is expected to be only the JSON object (optionally followed by one period).
    Returns (json_like_text or None, error_message).
    """
    core, _ = _strip_trailing_period(response)
    start = core.find('{')
    end = core.rfind('}')
    if start == -1 or end == -1 or end < start:
        return None, "The response must contain exactly one JSON object enclosed by '{' and '}', optionally followed by a single period."
    # Ensure no extra text before/after the JSON braces
    if core[:start].strip():
        return None, "Remove any text before the JSON object; only the JSON (plus a final period) is allowed."
    if core[end + 1:].strip():
        return None, "Remove any text after the JSON object; only the JSON (plus a final period) is allowed."
    return core[start:end + 1], ""


def _uses_double_colon_delimiters(json_like: str) -> Tuple[bool, str]:
    """
    Verify that key-value delimiters use '::' and not ':' (single).
    Also disallow ':::' (triple or more).
    """
    # At least one valid key:: occurrence
    if not re.findall(r'"\s*[^"]+\s*"\s*::', json_like):
        return False, "Use '::' (double colons) between every key and value (e.g., \"key\":: value)."
    # Disallow single-colon key-value separators
    if re.search(r'"\s*[^"]+\s*"\s*:(?=[^:])', json_like):
        return False, "Replace all single-colon ':' key-value separators with double colons '::'."
    # Disallow triple or longer colon runs
    if re.search(r':::+', json_like):
        return False, "Use exactly two colons '::' as the key-value delimiter (no more, no less)."
    return True, ""


def _to_standard_json(json_like: str) -> str:
    """
    Convert the custom '::' key-value delimiter into standard ':' for JSON parsing.
    """
    return json_like.replace("::", ":")


def _coerce_number(v: Any) -> Optional[float]:
    """
    Try to coerce a value into a float.
    Accepts int/float or numeric strings like '-12.34'.
    Returns float or None if not numeric.
    """
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if re.fullmatch(r'-?\d+(?:\.\d+)?', s):
            return float(s)
    return None


def _validate_required_keys(obj: Any) -> Tuple[bool, str]:
    """
    Ensure required keys exist and 'comparison_result' is boolean.
    """
    required = {"landmark_age", "mountain_height", "comparison_result"}
    if not isinstance(obj, dict):
        return False, "The JSON must be an object (use {...})."
    missing = required - obj.keys()
    if missing:
        return False, f"Missing required keys: {', '.join(sorted(missing))}. Include exactly: landmark_age, mountain_height, comparison_result."
    # comparison_result must be boolean (true/false in JSON)
    if not isinstance(obj.get("comparison_result"), bool):
        return False, "The value of \"comparison_result\" must be a boolean: true or false (lowercase JSON booleans)."
    return True, ""


def _validate_numeric_consistency(obj: dict) -> Tuple[bool, str]:
    """
    If both landmark_age and mountain_height are numeric, verify that comparison_result reflects (landmark_age > mountain_height).
    """
    a_num = _coerce_number(obj.get("landmark_age"))
    h_num = _coerce_number(obj.get("mountain_height"))
    if a_num is not None and h_num is not None:
        expected = a_num > h_num
        if obj["comparison_result"] != expected:
            return False, (
                "Incorrect comparison_result. It must reflect (landmark_age > mountain_height). "
                f"Given values imply {a_num} > {h_num} is {expected}. Set \"comparison_result\" to {str(expected).lower()}."
            )
    return True, ""


# ----------------------------
# Validators per constraint type
# ----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response consists solely of one JSON-like object (optionally followed by a period).
    - Keys are present: landmark_age, mountain_height, comparison_result.
    - Key-value delimiter uses '::' (double colons).
    - The JSON is structurally valid (after converting '::' to ':').
    - comparison_result is a boolean (true/false).
    - If numeric values are provided for both age and height, comparison_result matches (age > height).
    """
    json_like, err = _extract_core_json_text(response)
    if json_like is None:
        return False, err

    ok, msg = _uses_double_colon_delimiters(json_like)
    if not ok:
        return False, msg

    std_json = _to_standard_json(json_like)
    try:
        obj = json.loads(std_json)
    except json.JSONDecodeError as e:
        return False, (
            "Invalid JSON structure. Ensure: "
            "1) keys are double-quoted, 2) pairs are comma-separated, "
            "3) booleans are lowercase true/false, 4) numbers use digits only, "
            "and use '::' (double colons) between keys and values. "
            f"Parser error: {str(e)}"
        )

    ok, msg = _validate_required_keys(obj)
    if not ok:
        return False, msg

    ok, msg = _validate_numeric_consistency(obj)
    if not ok:
        return False, msg

    # Passed all checks
    return True, "The response satisfies the required JSON format with the correct keys and semantics."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period '.' (after any trailing whitespace).
    """
    if response.rstrip().endswith('.'):
        return True, "The response ends with a period as required."
    return False, "Append a single period '.' at the very end of the response, immediately after the closing '}', with no extra text following it."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the use of the delimiting identifier:
    - Each key-value pair must use double colons '::' (not a single ':', not ':::').
    - Confirm that the required keys appear with the '::' delimiter.
    """
    json_like, err = _extract_core_json_text(response)
    if json_like is None:
        return False, err

    ok, msg = _uses_double_colon_delimiters(json_like)
    if not ok:
        return False, msg

    # Ensure each required key uses the '::' delimiter explicitly
    required_keys = ["landmark_age", "mountain_height", "comparison_result"]
    missing_pattern = []
    for k in required_keys:
        if not re.search(rf'"\s*{re.escape(k)}\s*"\s*::', json_like):
            missing_pattern.append(k)
    if missing_pattern:
        return False, (
            "Each required key must be followed by the '::' delimiter. "
            f"Missing '::' after: {', '.join(missing_pattern)}. "
            "Example: {\"landmark_age\":: 120, \"mountain_height\":: 8848, \"comparison_result\":: true}."
        )

    return True, "All key-value pairs correctly use the '::' delimiter for the required identifiers."

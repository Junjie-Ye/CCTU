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
 You must ensure that in every interaction turn, you invoke **at most one unique tool type** simultaneously. Additionally, the 'social_media_metrics_tool' can be used **at most twice** in total across all interaction turns. All information must be obtained through tool calls, and you must correct and retry if any call fails. Your final answer **must contain a valid JSON object** containing the keys "ronaldo_followers", "messi_followers", and "difference_in_millions", each storing the corresponding numerical values retrieved through tool calls. The natural language **must end with a period (.)** to ensure proper sentence closure in the JSON value. Finally, the total number of interaction turns you take must **not exceed 3** to ensure efficiency.

response_constraints_non_length:
- idx 2: ('Response', 'Format', 'The agent\'s final response must contain a valid JSON object containing the keys "ronaldo_followers", "messi_followers", and "difference_in_millions", each storing the corresponding numerical values retrieved through tool calls.')
- idx 3: ('Response', 'Punctuation', 'The natural language in the JSON value must end with a period (.) to ensure proper sentence closure.')
"""

import json
from typing import Tuple, Optional, Any


# ------------------------- Helpers ------------------------- #
def _find_first_json_object(text: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Scan the input text to locate the first parseable top-level JSON object.
    Returns (json_str, start_index, end_index) if found and parseable, else (None, None, None).
    The scanner is brace- and quote-aware to avoid mismatches inside strings.
    """
    pos = 0
    n = len(text)
    while True:
        start = text.find("{", pos)
        if start == -1:
            return None, None, None

        depth = 0
        in_str = False
        escape = False
        for i in range(start, n):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start: i + 1]
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict):
                                return candidate, start, i + 1
                        except Exception:
                            # Not a valid JSON object; continue search from next "{"
                            break
        pos = start + 1


def _is_number(value: Any) -> bool:
    # Exclude booleans (bool is a subclass of int)
    return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)


# ------------------------- Validators ------------------------- #
def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validates that the response contains:
      - A valid JSON object.
      - The JSON object includes the keys: "ronaldo_followers", "messi_followers", "difference_in_millions".
      - Each of the above values is numeric (JSON numbers, not strings).
      - The reported "difference_in_millions" is numerically consistent with (ronaldo_followers - messi_followers)/1_000_000
        within a small tolerance.
    """
    json_str, start_idx, end_idx = _find_first_json_object(response)
    if json_str is None:
        return (
            False,
            "No valid JSON object was found in the response. Add a valid JSON object (not code-styled or pseudo-JSON), "
            'and ensure it includes the keys "ronaldo_followers", "messi_followers", and "difference_in_millions". '
            "Use standard JSON (double-quoted keys/strings, no trailing commas). Place it after the natural-language sentence."
        )

    try:
        obj = json.loads(json_str)
    except Exception as e:
        return (
            False,
            f"The detected JSON segment could not be parsed: {e}. Ensure the JSON is syntactically valid "
            "(double quotes for keys/strings, no trailing commas, numbers unquoted)."
        )

    required_keys = ["ronaldo_followers",
                     "messi_followers", "difference_in_millions"]
    missing = [k for k in required_keys if k not in obj]
    if missing:
        return (
            False,
            "The JSON object is missing required keys: "
            + ", ".join(f'"{k}"' for k in missing)
            + '. Include them as JSON numbers, e.g., {"ronaldo_followers": 123456789, "messi_followers": 98765432, "difference_in_millions": 24.69}.'
        )

    rf = obj.get("ronaldo_followers")
    mf = obj.get("messi_followers")
    dm = obj.get("difference_in_millions")

    # Type checks: must be JSON numbers (not strings)
    type_errors = []
    if not _is_number(rf):
        type_errors.append(
            '"ronaldo_followers" must be a JSON number (do not wrap in quotes or include commas/units).')
    if not _is_number(mf):
        type_errors.append(
            '"messi_followers" must be a JSON number (do not wrap in quotes or include commas/units).')
    if not _is_number(dm):
        type_errors.append(
            '"difference_in_millions" must be a JSON number (do not wrap in quotes or include commas/units).')

    if type_errors:
        return (
            False,
            "Type validation failed: "
            + " ".join(type_errors)
            + " Provide raw numeric literals only, e.g., 215000000, not \"215,000,000\" or \"215M\"."
        )

    # Consistency check for difference_in_millions
    try:
        calc_dm = (float(rf) - float(mf)) / 1_000_000.0
        tolerance = 1e-3  # acceptable absolute difference in millions
        if abs(float(dm) - calc_dm) > tolerance:
            return (
                False,
                f'The value of "difference_in_millions" ({dm}) is inconsistent with the follower counts. '
                f"It should be approximately (ronaldo_followers - messi_followers) / 1_000_000 = {calc_dm:.6f}. "
                "Update the difference to match the computed value within a small rounding tolerance."
            )
    except Exception as e:
        return (
            False,
            f"An error occurred while checking numerical consistency: {e}. Ensure all three values are valid numbers."
        )

    return True, "Format validation passed: valid JSON detected with required numeric keys and consistent difference."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validates that the natural-language explanation preceding the JSON object ends with a period ('.').
    If there is no natural-language text before the JSON object, this fails.
    """
    json_str, start_idx, _ = _find_first_json_object(response)
    if json_str is None or start_idx is None:
        return (
            False,
            "No JSON object detected, so punctuation of the preceding natural-language sentence cannot be verified. "
            "Provide one concise sentence before the JSON and ensure it ends with a period, then place the JSON object."
        )

    pre_text = response[:start_idx].strip()
    if not pre_text:
        return (
            False,
            "No natural-language explanation found before the JSON object. Add a concise sentence before the JSON and "
            "ensure it ends with a period, e.g., 'Here are the retrieved metrics.' followed by the JSON object."
        )

    # Check last non-whitespace character is '.'
    last_char = pre_text[-1]
    if last_char != ".":
        return (
            False,
            "The natural-language sentence immediately preceding the JSON object must end with a period ('.'). "
            "Revise the text so its final character before the JSON is a period."
        )

    return True, "Punctuation validation passed: the pre-JSON natural-language sentence ends with a period."

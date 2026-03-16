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
 The answer must be obtained using the provided tools. At most 6 interaction rounds are allowed to complete the task, and the solution must involve between 2 and 6 tool calls. If the agent invokes the timezone_finder tool, it must first call the historical_event_locator tool. Additionally, the `historical_event_locator` may be called at most 2 times, and the `timezone_finder` may be called at most 2 times. The final answer must contain a valid JSON object with the time zone details as the value for the key "timezone", the JSON response must end with a period, and the response must include the delimiter "###" before the JSON answer to clearly separate the explanation from the JSON result.

response_constraints_non_length:
- idx 2: ('Response', 'Format', 'The final answer must contain a valid JSON object with the time zone details as the value for the key "timezone".')
- idx 3: ('Response', 'Punctuation', 'The final JSON response must end with a period.')
- idx 5: ('Response', 'Identifiers', '(Response, Delimiting identifier, The response must include the delimiter "###" before the final JSON answer to clearly separate the explanation from the JSON result.)')
"""

import json
import re
from typing import Tuple, Optional


DELIMITER = "###"


def _rfind_delimiter(text: str) -> int:
    """Return the index of the last occurrence of the delimiter, or -1 if not found."""
    return text.rfind(DELIMITER)


def _skip_whitespace(text: str, start: int) -> int:
    """Return the index of the first non-whitespace character at or after start."""
    i = start
    while i < len(text) and text[i].isspace():
        i += 1
    return i


def _extract_json_object_after_delimiter(response: str) -> Tuple[Optional[str], Optional[int], Optional[int], str]:
    """
    Locate the final JSON object that must appear after the last '###' delimiter.
    Returns (json_str, start_idx, end_idx_inclusive, error_msg).
      - json_str is the exact substring of the JSON object (without trailing period).
      - start_idx is the index of '{' starting the JSON object.
      - end_idx_inclusive is the index of the matching '}'.
      - error_msg is empty on success, otherwise a descriptive English message.
    """
    delim_idx = _rfind_delimiter(response)
    if delim_idx == -1:
        return None, None, None, "Missing required delimiter '###'. Place '###' on its own line immediately before the final JSON answer."

    i = _skip_whitespace(response, delim_idx + len(DELIMITER))
    if i >= len(response):
        return None, None, None, "No content found after '###'. Place a JSON object immediately after the delimiter."
    if response[i] != "{":
        return None, None, None, "The final answer after '###' must start with a JSON object '{...}'. Do not add text between '###' and the JSON."

    # Extract JSON object by matching braces, respecting strings and escapes
    depth = 0
    in_string = False
    escape = False
    start_idx = i
    end_idx = None

    for pos in range(i, len(response)):
        ch = response[pos]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_idx = pos
                    break

    if end_idx is None:
        return None, None, None, "Unmatched braces in the JSON object after '###'. Ensure the JSON object is complete and syntactically valid."

    json_str = response[start_idx: end_idx + 1]

    # Validate JSON loads independently (without any trailing period)
    try:
        parsed = json.loads(json_str)
        if not isinstance(parsed, dict):
            return None, None, None, "The final answer must be a JSON object (e.g., {\"timezone\": \"Continent/City\"}), not an array or a scalar."
    except json.JSONDecodeError as e:
        return None, None, None, f"Invalid JSON object after '###': {e}. Ensure there is no trailing period inside the JSON and that keys/strings use double quotes."

    return json_str, start_idx, end_idx, ""


def _validate_timezone_value(value) -> Optional[str]:
    """
    Validate that the 'timezone' value contains time zone details.
    Accepts:
      - Non-empty string (e.g., 'America/New_York' or 'UTC+01:00')
      - Non-empty object/dict with one or more fields (e.g., {'name': 'America/New_York', 'offset': '-05:00'})
    Returns None if valid, otherwise an English error message.
    """
    if isinstance(value, str):
        if value.strip() == "":
            return "The 'timezone' value must be a non-empty string (e.g., 'America/New_York')."
        return None
    if isinstance(value, dict):
        if len(value) == 0:
            return "The 'timezone' object must include at least one detail (e.g., name, id, offset, abbreviation)."
        return None
    return "The 'timezone' value must be either a non-empty string or a non-empty object with timezone details."


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Response Format Constraints:
      - The final answer must contain a valid JSON object.
      - The JSON must be the final answer content after '###'.
      - The JSON must include a 'timezone' key holding time zone details (non-empty string or non-empty object).
    """
    json_str, start_idx, end_idx, err = _extract_json_object_after_delimiter(
        response)
    if err:
        return False, (
            err
            + " Provide the final answer as: an explanation, then a line with '###', then a single JSON object. "
            + "Example:\n###\n{\"timezone\": \"America/New_York\"}."
        )

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON after '###': {e}. Ensure the JSON object is well-formed and uses double quotes."

    if "timezone" not in data:
        return False, "The JSON object must include the key 'timezone'. Example: ### then {'timezone': 'America/New_York'} (use double quotes) and end the response with a period outside the JSON."

    tz_err = _validate_timezone_value(data["timezone"])
    if tz_err:
        return False, tz_err + " Example valid outputs: ### then {\"timezone\": \"Europe/London\"}. or ### then {\"timezone\": {\"name\": \"Europe/London\", \"offset\": \"+00:00\"}}."

    return True, "OK"


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Punctuation Constraint:
      - The final JSON response must end with a period.
      - The period must be outside the JSON (i.e., after the closing '}'), and nothing except whitespace may follow it.
    """
    json_str, start_idx, end_idx, err = _extract_json_object_after_delimiter(
        response)
    if err:
        # Still check general ending, but provide targeted guidance
        trimmed = response.rstrip()
        ends_with_period = trimmed.endswith(".")
        if not ends_with_period:
            return False, "The final response must end with a single period. Add a '.' at the very end of the output."
        return False, (
            err
            + " Also ensure the period is outside the JSON. Example:\n###\n{\"timezone\": \"America/New_York\"}."
        )

    # Check that after the JSON object, the only allowed content is optional whitespace, a single '.', then optional whitespace to the end.
    trailing = response[end_idx + 1:]
    if not re.fullmatch(r"\s*\.\s*\Z", trailing, flags=re.DOTALL):
        return False, "Add exactly one period after the closing '}' of the JSON, and do not include any other characters after it. Example: {...}."

    # Also ensure the overall response ends with a period (ignoring trailing whitespace)
    if not response.rstrip().endswith("."):
        return False, "The final response must end with a period. Place the '.' right after the JSON object."

    return True, "OK"


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Identifiers/Delimiter Constraint:
      - The response must include the delimiter '###' immediately before the final JSON answer.
      - There must be no non-whitespace text between '###' and the opening '{' of the JSON.
    """
    delim_idx = _rfind_delimiter(response)
    if delim_idx == -1:
        return False, "Insert the delimiter '###' on a line by itself immediately before the final JSON answer."

    # Verify that the JSON starts right after the delimiter (allowing only whitespace/newlines in between)
    after_delim_idx = _skip_whitespace(response, delim_idx + len(DELIMITER))
    if after_delim_idx >= len(response) or response[after_delim_idx] != "{":
        return False, "Place the JSON object immediately after '###' with no intervening text. Example:\nExplanation...\n###\n{\"timezone\": \"America/New_York\"}."

    # Ensure we can actually extract a valid JSON object after the delimiter
    json_str, start_idx, end_idx, err = _extract_json_object_after_delimiter(
        response)
    if err:
        return False, "A valid JSON object must follow '###'. " + err

    return True, "OK"

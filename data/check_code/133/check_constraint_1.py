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
 The answer must be formatted as a valid JSON object containing the two distances in miles: one for the B-50 Superfortress Lucky Lady II's flight and one for the California Zephyr train route, with the keys "flight_distance" and "train_distance", respectively. The agent must include an explicit key-value pair "separator_tag": "DISTANCE_SEPARATOR" immediately after the flight_distance entry within the JSON object, creating a bridge between the two distance fields.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must be formatted as a valid JSON object containing the two distances in miles: one for the B-50 Superfortress Lucky Lady II\'s flight and one for the California Zephyr train route, with the keys "flight_distance" and "train_distance", respectively.')
- idx 1: ('Response', 'Identifiers', '(Response, Delimiting identifier, The agent must include an explicit key-value pair "separator_tag": "DISTANCE_SEPARATOR" immediately after the flight_distance entry within the JSON object, creating a bridge between the two distance fields.)')
"""

import json
from collections import OrderedDict
from typing import Tuple, Optional, Union

# ----------------------------
# Helper utilities
# ----------------------------


def _load_ordered_json(response: str) -> Tuple[Optional[OrderedDict], Optional[str]]:
    """
    Parse response as JSON preserving key order. Return (obj, error_message).
    obj is an OrderedDict when successful; otherwise None with a detailed error message.
    """
    # Quick check to discourage any prose outside JSON
    stripped = response.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None, ("The response must be exactly one JSON object with no text before or after. "
                      "Start with '{' and end with '}'.")
    try:
        obj = json.loads(response, object_pairs_hook=OrderedDict)
    except json.JSONDecodeError as e:
        return None, (f"Invalid JSON. Ensure the output is a single JSON object only. "
                      f"JSON parsing error: {e}")
    if not isinstance(obj, OrderedDict):
        return None, ("The top-level JSON must be an object (dictionary). "
                      "Do not output arrays or primitive values.")
    return obj, None


def _is_number(value: Union[int, float, bool, str]) -> bool:
    """
    Return True if value is a real JSON number (int or float) and not a boolean.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)

# ----------------------------
# Validators for response constraints
# ----------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate the 'format' constraint:
    - The response must be a valid JSON object.
    - It must contain the two distance fields in miles with keys:
      'flight_distance' and 'train_distance'.
    - The values for these two keys must be JSON numbers (not strings, not with units).
    - The relative order of distance keys must be: 'flight_distance' comes before 'train_distance'.
      (Other keys may appear, including the required 'separator_tag' which should sit between them
       per the identifiers constraint, but this function only enforces relative order of the two distances.)
    """
    obj, err = _load_ordered_json(response)
    if err:
        return False, (err + " Example of a correct structure: "
                       '{"flight_distance": 0, "separator_tag": "DISTANCE_SEPARATOR", "train_distance": 0}')
    keys = list(obj.keys())

    # Check presence of required keys
    missing = [k for k in (
        "flight_distance", "train_distance") if k not in obj]
    if missing:
        return False, ("Missing required key(s): " + ", ".join(missing) +
                       ". Include both 'flight_distance' and 'train_distance' as top-level keys.")

    # Check values are numbers (miles) and not strings or with units
    fd_val = obj["flight_distance"]
    td_val = obj["train_distance"]
    if not _is_number(fd_val):
        return False, ("'flight_distance' must be a JSON number representing miles (e.g., 23145.7). "
                       "Do not quote it and do not add units. Write 23145.7, not '23145.7' or '23145.7 miles'.")
    if not _is_number(td_val):
        return False, ("'train_distance' must be a JSON number representing miles (e.g., 2438). "
                       "Do not quote it and do not add units. Write 2438, not '2438' or '2438 miles'.")

    # Optional plausibility: distances should be non-negative
    if fd_val < 0 or td_val < 0:
        return False, ("Distances must be non-negative numbers in miles. "
                       "Ensure both 'flight_distance' and 'train_distance' are >= 0.")

    # Enforce relative key order: flight_distance before train_distance
    fd_idx = keys.index("flight_distance")
    td_idx = keys.index("train_distance")
    if not (fd_idx < td_idx):
        return False, ("Key ordering must place 'flight_distance' before 'train_distance'. "
                       "A correct example with the required separator is: "
                       '{"flight_distance": 0, "separator_tag": "DISTANCE_SEPARATOR", "train_distance": 0}')

    return True, "The response is a valid JSON object with correctly typed distance fields and proper relative order."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate the 'identifiers' constraint:
    - The JSON must include an explicit key-value pair:
      'separator_tag': 'DISTANCE_SEPARATOR'.
    - The 'separator_tag' must appear immediately after 'flight_distance' in the object key order.
    - The 'train_distance' key must come after 'separator_tag', forming a bridge between the two distance fields.
    """
    obj, err = _load_ordered_json(response)
    if err:
        return False, (err + " Ensure the object includes the separator like: "
                       '{"flight_distance": 0, "separator_tag": "DISTANCE_SEPARATOR", "train_distance": 0}')

    keys = list(obj.keys())

    # Check presence and exact value of separator_tag
    if "separator_tag" not in obj:
        return False, ("Missing required identifier bridge. Insert the exact pair "
                       '"separator_tag": "DISTANCE_SEPARATOR" immediately after "flight_distance".')
    sep_val = obj["separator_tag"]
    if not isinstance(sep_val, str) or sep_val != "DISTANCE_SEPARATOR":
        return False, ('The "separator_tag" value must be the exact string "DISTANCE_SEPARATOR". '
                       'Example: "separator_tag": "DISTANCE_SEPARATOR"')

    # Check positional ordering: flight_distance, separator_tag, train_distance
    if "flight_distance" not in obj or "train_distance" not in obj:
        return False, ("Both 'flight_distance' and 'train_distance' must exist alongside 'separator_tag'. "
                       "Provide all three keys in order.")
    fd_idx = keys.index("flight_distance")
    sep_idx = keys.index("separator_tag")
    td_idx = keys.index("train_distance")

    # separator_tag must be immediately after flight_distance
    if sep_idx != fd_idx + 1:
        return False, ("Ensure key order places 'separator_tag' immediately after 'flight_distance'. "
                       "Correct order starts as: "
                       '..."flight_distance": <number>, "separator_tag": "DISTANCE_SEPARATOR", "train_distance": <number>...')
    # train_distance must come after separator_tag to form the bridge
    if not (td_idx > sep_idx):
        return False, ("Place 'train_distance' after 'separator_tag' so the separator bridges the two distances. "
                       "Correct order: flight_distance -> separator_tag -> train_distance.")

    return True, ('The response correctly includes "separator_tag": "DISTANCE_SEPARATOR" immediately after '
                  '"flight_distance" and before "train_distance".')

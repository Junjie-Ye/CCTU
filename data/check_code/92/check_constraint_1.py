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
 The answer must be concise, contain at most 20 words, be formatted as a valid JSON object with a single key "answer" containing the result. The final identified sport must be explicitly stated and enclosed within double square brackets (e.g., [[Baseball]]) to serve as the unique identifier for the answer. if the agent intends to invoke any tool in the sequence [capital_identifier, literary_award_search, author_works_finder, book_to_movie_adapter, film_metadata_retriever, biographical_data_search, country_sport_identifier], the preceding tools in the sequence must be executed strictly beforehand, and each tool may be invoked at most once during execution.

response_constraints_non_length:
- idx 1: ('Response', 'Format', '(Response, Format, "The entire response must be a valid JSON object with a single key \'answer\' containing the final result. The JSON must adhere to proper syntax and be parseable without errors.")')
- idx 2: ('Response', 'Identifiers', 'The final identified sport must be explicitly stated and enclosed within double square brackets (e.g., [[Baseball]]) to serve as the unique identifier for the answer.')
"""

import json
import re
from typing import Tuple, Any


# ---------------------------
# Shared helpers
# ---------------------------

def _parse_entire_json(response: str) -> Tuple[bool, Any, str]:
    """
    Parse the entire response as JSON and ensure there is no extra content.
    Returns (ok, parsed_obj, error_message).
    """
    if response is None:
        return False, None, "Response is empty. Provide a JSON object like {\"answer\": \"[[Sport]]\"}."
    text = response.strip()

    # Disallow code fences or leading/trailing commentary
    if text.startswith("```") or text.endswith("```"):
        return False, None, "Remove code fences. Output must be only a JSON object, not wrapped in triple backticks."

    try:
        decoder = json.JSONDecoder()
        obj, end = decoder.raw_decode(text)
        # Ensure no trailing non-whitespace content after the JSON object
        remainder = text[end:].strip()
        if remainder:
            return False, None, "Extra characters after the JSON object. Output only the JSON object with no trailing text."
        return True, obj, ""
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON syntax: {e}. Output must be a single JSON object like {{\"answer\": \"[[Sport]]\"}}."


def _ensure_answer_object(obj: Any) -> Tuple[bool, str]:
    """
    Validate top-level structure: dict with exactly one key 'answer' whose value is a string.
    Returns (ok, error_message).
    """
    if not isinstance(obj, dict):
        return False, "Top-level JSON must be an object. Provide exactly one object with the single key 'answer'."

    keys = list(obj.keys())
    if "answer" not in obj:
        return False, "Missing key 'answer'. Provide a JSON object with exactly one key named 'answer'."
    if len(keys) != 1:
        return False, "JSON must contain exactly one key 'answer' and no other keys."

    if not isinstance(obj["answer"], str):
        return False, "The value of 'answer' must be a string (e.g., \"[[Baseball]]\")."

    return True, ""


# ---------------------------
# Validators for response constraints
# ---------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    (Response, Format)
    The entire response must be a valid JSON object with a single key 'answer' containing the final result.
    The JSON must adhere to proper syntax and be parseable without errors.
    """
    ok, obj, err = _parse_entire_json(response)
    if not ok:
        return False, ("Format error: " + err +
                       " Ensure your entire message is exactly one JSON object with a single key 'answer'.")

    ok, err2 = _ensure_answer_object(obj)
    if not ok:
        return False, ("Format error: " + err2 +
                       " Example of correct format: {\"answer\": \"[[Sport]]\"}.")

    return True, "Format is valid."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    (Response, Identifiers)
    The final identified sport must be explicitly stated and enclosed within double square brackets (e.g., [[Baseball]]).
    The 'answer' value should be exactly the bracketed identifier with no extra text.
    """
    ok, obj, err = _parse_entire_json(response)
    if not ok:
        return False, ("Identifier check blocked by format issue: " + err +
                       " First, ensure the output is a single JSON object containing only the 'answer' key.")

    ok, err2 = _ensure_answer_object(obj)
    if not ok:
        return False, ("Identifier check blocked by format issue: " + err2 +
                       " Provide exactly one key 'answer' whose value is a string like \"[[Sport]]\".")

    answer_val = obj["answer"]

    # Must be exactly [[...]] with no other surrounding text; inner cannot be empty or contain brackets.
    pattern = r'^\s*\[\[[^\[\]\n]+\]\]\s*$'
    if not re.match(pattern, answer_val):
        return False, (
            "Identifier error: The 'answer' value must be exactly a double-bracketed sport identifier with no extra text, "
            "for example: \"[[Baseball]]\". Do not add explanations, punctuation, or additional content outside the brackets."
        )

    return True, "Identifier format is valid: 'answer' contains a single [[Sport]] token."

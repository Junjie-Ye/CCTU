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

r"""
refine_constraint:
 The answer must be presented in a valid JSON format, ensuring correct syntax with key-value pairs, commas, colons, and quotation marks, and must be fully parsed without errors. Additionally, the JSON response must include the key "Prüm_Explosion_Casualties" followed by a colon and the value retrieved for the Prüm explosion, and the key "SS_Noromic_Fire_Casualties" followed by a colon and the value retrieved for the SS Noromic fire, separated by a comma for clarity. At least one interaction turn must involve invoking at least 2 tool calls simultaneously. The response must be at least 150 characters long to ensure sufficient detail and completeness. The JSON must not include any invalid punctuation, such as trailing commas or semicolons, to ensure valid syntax. The agent must complete this task with no more than 5 tool calls in total.

response_constraints_non_length:
- idx 1: ('Response', 'Format', 'The answer must be presented in a valid JSON format, ensuring correct syntax with key-value pairs, commas, colons, and quotation marks, and must be fully parsed without errors.')
- idx 2: ('Response', 'Identifiers', '(Main Category, Delimiting identifier, The JSON response must include the key "Prüm_Explosion_Casualties" followed by a colon and the value retrieved for the Prüm explosion, and the key "SS_Noromic_Fire_Casualties" followed by a colon and the value retrieved for the SS Noromic fire, separated by a comma for clarity.)')
- idx 4: ('Response', 'Punctuation', 'Exclude punctuation (Do not include any invalid punctuation such as trailing commas or semicolons in the JSON response to ensure valid syntax.)')
"""

import json
import re
from typing import Tuple, Any, List, Optional


# -----------------------------
# Helper utilities
# -----------------------------

def _try_parse_json(response: str) -> Tuple[bool, Optional[Any], str]:
    """
    Try to parse the response as JSON.
    Returns (ok, obj, error_message).
    """
    text = response.strip()
    try:
        obj = json.loads(text)
        return True, obj, "OK"
    except json.JSONDecodeError as e:
        # Build a detailed, actionable error message
        pointer = f"line {e.lineno}, column {e.colno}, char {e.pos}"
        msg = (
            f"Invalid JSON: {e.msg} at {pointer}. "
            "Make sure to use double quotes for keys/strings, no trailing commas, "
            "no semicolons, and no comments. Example of a valid object: "
            '{"key": "value", "another_key": 123}'
        )
        return False, None, msg


def _outside_string_mask(s: str) -> List[bool]:
    """
    Return a boolean mask indicating whether each character is outside of JSON string literals.
    Considers JSON string rules with double quotes and backslash escapes.
    """
    mask = [True] * len(s)
    inside = False
    escape = False
    for i, ch in enumerate(s):
        if inside:
            mask[i] = False
            if escape:
                escape = False
            else:
                if ch == '\\':
                    escape = True
                elif ch == '"':
                    inside = False
        else:
            if ch == '"':
                mask[i] = False
                inside = True
    return mask


def _find_semicolons_outside_strings(s: str) -> List[int]:
    """
    Find indices of semicolons that appear outside string literals.
    """
    mask = _outside_string_mask(s)
    return [i for i, ch in enumerate(s) if ch == ';' and mask[i]]


def _find_trailing_commas(s: str) -> List[int]:
    r"""
    Detect trailing commas outside string literals, i.e., a comma followed by optional
    whitespace and then a closing brace or bracket: ,\s*[}\]]
    Returns list of comma indices considered trailing.
    """
    mask = _outside_string_mask(s)
    bad_indices: List[int] = []
    i = 0
    n = len(s)
    whitespace = set([' ', '\t', '\r', '\n'])
    while i < n:
        if s[i] == ',' and mask[i]:
            j = i + 1
            while j < n and s[j] in whitespace:
                j += 1
            if j < n and s[j] in ['}', ']']:
                bad_indices.append(i)
        i += 1
    return bad_indices


def _snippet(s: str, idx: int, radius: int = 20) -> str:
    """
    Return a short snippet around the given index to help pinpoint issues.
    """
    start = max(0, idx - radius)
    end = min(len(s), idx + radius + 1)
    caret_pos = idx - start
    snippet_text = s[start:end].replace('\n', '\\n')
    caret_line = ' ' * caret_pos + '^'
    return f"...{snippet_text}...\n   {caret_line}"


# -----------------------------
# Validators
# -----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that:
    - The response is valid JSON (fully parsable without errors).
    - The root value is a JSON object (dictionary).
    """
    ok, obj, err = _try_parse_json(response)
    if not ok:
        return False, (
            f"{err} Ensure the response is a single, valid JSON object. "
            "Common fixes: quote all keys with double quotes, remove any trailing commas, "
            "remove semicolons, and avoid comments or extra text outside the JSON."
        )

    if not isinstance(obj, dict):
        return False, (
            "The response must be a JSON object (dictionary) at the top level. "
            "Wrap all key-value pairs within curly braces, e.g.: "
            '{"Prüm_Explosion_Casualties": "value", "SS_Noromic_Fire_Casualties": "value"}'
        )

    return True, "Valid JSON format: the response parses correctly and is a top-level object."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the JSON includes the required top-level keys:
    - 'Prüm_Explosion_Casualties'
    - 'SS_Noromic_Fire_Casualties'
    And that their values are present (not null and not an empty string).
    """
    ok, obj, err = _try_parse_json(response)
    if not ok:
        return False, (
            f"{err} After fixing the JSON syntax, ensure it contains both required keys "
            '"Prüm_Explosion_Casualties" and "SS_Noromic_Fire_Casualties" at the top level, '
            "spelled exactly (including the umlaut ü in 'Prüm')."
        )

    if not isinstance(obj, dict):
        return False, (
            "Identifiers must be present at the top level of a JSON object. "
            "Ensure the root is an object and includes the two required keys."
        )

    required_keys = ["Prüm_Explosion_Casualties", "SS_Noromic_Fire_Casualties"]
    missing = [k for k in required_keys if k not in obj]
    if missing:
        return False, (
            "Missing required key(s): " +
            ", ".join(f'"{k}"' for k in missing) + ". "
            "Add them exactly as specified (including diacritics), for example: "
            '{"Prüm_Explosion_Casualties": "retrieved value", '
            '"SS_Noromic_Fire_Casualties": "retrieved value"}'
        )

    # Check that values are present (not None and not empty string)
    empty_like = []
    for k in required_keys:
        v = obj.get(k, None)
        if v is None:
            empty_like.append(k)
        elif isinstance(v, str) and v.strip() == "":
            empty_like.append(k)

    if empty_like:
        return False, (
            "The following required keys have empty or null values: "
            + ", ".join(f'"{k}"' for k in empty_like) + ". "
            "Provide concrete, tool-derived values (non-empty strings or numbers)."
        )

    return True, (
        'Identifiers OK: The JSON includes both "Prüm_Explosion_Casualties" and '
        '"SS_Noromic_Fire_Casualties" with present values.'
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate punctuation rules:
    - No semicolons (;) outside string literals.
    - No trailing commas before closing } or ] (outside string literals).
    Note: A valid JSON parse will also fail if trailing commas exist, but we report them explicitly.
    """
    text = response.strip()

    semis = _find_semicolons_outside_strings(text)
    trails = _find_trailing_commas(text)

    issues: List[str] = []

    if semis:
        examples = "\n".join(
            f"Semicolon at index {i}:\n{_snippet(text, i)}" for i in semis[:3]
        )
        more = "" if len(
            semis) <= 3 else f"\n(+ {len(semis) - 3} more occurrences)"
        issues.append(
            "Invalid punctuation: semicolons are not allowed in JSON outside strings. "
            "Replace semicolons with commas only where appropriate in arrays/objects.\n"
            + examples + more
        )

    if trails:
        examples = "\n".join(
            f"Trailing comma at index {i}:\n{_snippet(text, i)}" for i in trails[:3]
        )
        more = "" if len(
            trails) <= 3 else f"\n(+ {len(trails) - 3} more occurrences)"
        issues.append(
            "Invalid punctuation: trailing commas before a closing brace/bracket are not allowed in JSON. "
            "Remove the extra comma.\n" + examples + more
        )

    if issues:
        return False, (
            "Punctuation errors detected:\n- " + "\n- ".join(issues) +
            "\nEnsure the response contains only valid JSON punctuation: "
            "commas between items, colons between keys and values, and no semicolons or trailing commas."
        )

    return True, "Punctuation is valid: no semicolons outside strings and no trailing commas were detected."

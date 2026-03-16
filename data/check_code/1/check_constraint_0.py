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
 The answer must be formatted as a valid JSON object containing a "successor" key with the full name of the successor as its value. The agent must use the `political_successor_finder` tool no more than one time to determine this information.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "JSON (Mandates that the agent's entire response must be structured as a valid JSON object, adhering to proper syntax rules including key-value pairs, correct use of commas, colons, and quotation marks, and ensuring that the JSON can be successfully parsed without errors.)")
"""


from typing import Tuple
import json
import re


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the entire response is a valid JSON object and complies with the task's format requirement:
    - The response must be ONLY a JSON object (no prose, no section headers, no code fences).
    - It must be parseable JSON using double quotes.
    - It must contain a "successor" key.
    - The value for "successor" must be a non-empty string (the full name).
    Returns:
        (is_valid, message)
        message is an actionable English description of what to fix if invalid.
    """
    if response is None:
        return False, 'Response is None. Output must be a single JSON object like {"successor": "Full Name"} with no additional text.'

    # Quick checks for common formatting violations.
    if "```" in response:
        return False, 'Remove code fences. The entire output must be raw JSON only, e.g., {"successor": "Full Name"} with no backticks.'
    if any(tag in response for tag in ["[THOUGHT]", "[ACTION]", "[REFLECTION]", "[FINAL ANSWER]"]):
        return False, 'Do not include any section headers. Output must be only a JSON object like {"successor": "Full Name"}.'

    # Strip BOM and whitespace
    text = response.lstrip("\ufeff").strip()
    if not text:
        return False, 'Empty response. Provide a JSON object like {"successor": "Full Name"}.'

    # Attempt strict JSON parsing
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return False, f'Invalid JSON: {e.msg} at position {e.pos}. Ensure valid JSON with double quotes and no trailing text. Example: {{"successor": "Full Name"}}'

    # The top-level must be a JSON object
    if not isinstance(parsed, dict):
        return False, 'Top-level JSON must be an object. Output must look like {"successor": "Full Name"}, not an array or string.'

    # Must contain "successor" key
    if "successor" not in parsed:
        return False, 'Missing required key "successor". Include it exactly as spelled: {"successor": "Full Name"}.'

    # Validate the "successor" value
    val = parsed["successor"]
    if not isinstance(val, str):
        return False, 'The value of "successor" must be a string. Example: {"successor": "Full Name"}.'
    if not val.strip():
        return False, 'The "successor" value is empty. Provide a non-empty full name string, e.g., {"successor": "Full Name"}.'

    # Optional sanity checks to help avoid common mistakes (non-fatal if they pass)
    # Reject placeholder-like values
    placeholder_patterns = [
        r"<[^>]+>",        # e.g., <name>
        r"\bTBD\b",
        r"\bUNKNOWN\b",
        r"\bN/?A\b",
        r"\bNone\b",
        r"\bnull\b",
    ]
    if any(re.search(p, val, flags=re.IGNORECASE) for p in placeholder_patterns):
        return False, 'The "successor" value looks like a placeholder. Provide the actual full name string, e.g., {"successor": "Jane Doe"}.'

    # Encourage minimal keys (not required, so we do not fail if extra keys exist)
    extra_keys = [k for k in parsed.keys() if k != "successor"]
    if extra_keys:
        return True, f'Valid JSON format detected. Consider returning only the required key "successor" to be safe. Extra keys present: {extra_keys}'

    return True, 'Valid JSON format with required "successor" key and a non-empty string value.'

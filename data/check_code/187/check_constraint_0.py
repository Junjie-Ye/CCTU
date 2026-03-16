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
 Your final answer must be presented in a valid JSON format, including both the numerical result and the reasoning process. The agent must not call the `population_data_retriever` tool more than once, the total number of tool calls must be at most 10, and the agent must perform at least one interaction turn where it invokes at least two unique tool type simultaneously. Additionally, the response must be between 500 and 1500 characters long, inclusive, to ensure sufficient detail and conciseness.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "JSON (Mandates that the agent's entire response must be structured as a valid JSON object, adhering to proper syntax rules including key-value pairs, correct use of commas, colons, and quotation marks, and ensuring that the JSON can be successfully parsed without errors.)")
"""

import json
import re
from typing import Tuple, List


def _make_error_context(text: str, lineno: int, colno: int, context_radius: int = 40) -> str:
    """
    Build a small caret-marked context snippet around a JSON error location.
    """
    lines = text.splitlines()
    if 1 <= lineno <= len(lines):
        line = lines[lineno - 1]
        start = max(0, colno - 1 - context_radius)
        end = min(len(line), colno - 1 + context_radius)
        snippet = line[start:end]
        caret_pos = (colno - 1) - start
        caret_line = " " * max(0, caret_pos) + "^"
        return f"Line {lineno}, column {colno}:\n{snippet}\n{caret_line}"
    return "No context available."


def _detect_common_json_mistakes(text: str) -> List[str]:
    """
    Heuristics to suggest fixes for typical JSON formatting mistakes.
    """
    hints = []

    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        hints.append(
            "Remove Markdown code fences (```); output must be raw JSON only.")

    # Single-quoted keys or strings are invalid in strict JSON
    if re.search(r"(?:^|[{,\s])\s*'[^']*'\s*:", text):
        hints.append(
            "Use double quotes for all keys: \"key\": \"value\" (single quotes are invalid).")
    if re.search(r'":\s*\'', text) or re.search(r"':\s*\"", text):
        hints.append(
            "Use double quotes for string values as well; single-quoted strings are invalid.")

    # Trailing commas
    if re.search(r",\s*[}\]]", text):
        hints.append("Remove trailing commas before closing } or ].")

    # JavaScript-only tokens
    if re.search(r"\bNaN\b|\bInfinity\b|-Infinity", text):
        hints.append(
            "Replace NaN/Infinity with valid JSON values (e.g., numbers or null).")

    # Comments are not allowed in JSON
    if re.search(r"(^|\s)//", text) or re.search(r"/\*", text):
        hints.append(
            "Remove comments; JSON does not allow // or /* */ comments.")

    # Unescaped control characters inside strings (rough heuristic)
    if re.search(r'".*[\x00-\x1F].*"', text):
        hints.append(
            "Escape control characters in strings (e.g., newline as \\n, tab as \\t).")

    # Missing top-level braces (common when outputting key/value pairs without {})
    if not stripped.startswith("{") or not stripped.endswith("}"):
        hints.append(
            "Ensure the entire response is a single JSON object enclosed by { }.")

    return hints


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the entire response is a valid, parseable JSON object (not an array or scalar).
    Returns:
      - (True, guidance) if valid.
      - (False, error_explanation) if invalid, with actionable, detailed instructions.
    """
    # Quick check for accidental Markdown fences
    s = response.strip()
    if s.startswith("```") and s.endswith("```"):
        return (
            False,
            "Invalid JSON: Detected Markdown code fences. Output must be raw JSON only, without ``` fences. "
            "Provide a single JSON object enclosed by { } with double-quoted keys and values where appropriate."
        )

    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as e:
        hints = _detect_common_json_mistakes(response)
        context = _make_error_context(response, e.lineno, e.colno)
        hint_text = (" Hints: " + "; ".join(hints)) if hints else ""
        return (
            False,
            f"Invalid JSON: {e.msg}. {context}{hint_text} "
            "General rules: use double quotes for all keys and string values, no trailing commas, "
            "no comments, and ensure the entire output is a single JSON object."
        )

    if not isinstance(parsed, dict):
        return (
            False,
            "Format violation: The top-level JSON value must be an object (i.e., enclosed by { }). "
            "Do not return an array or a primitive. Include key-value pairs only at the root."
        )

    return (
        True,
        "Valid JSON object detected. To stay compliant: keep only a single top-level object, use double-quoted keys, "
        "avoid comments/trailing commas, and do not wrap the output in Markdown fences. "
        "Optionally ensure fields clearly separate a numerical result and a reasoning narrative, and keep the total length within 500–1500 characters."
    )

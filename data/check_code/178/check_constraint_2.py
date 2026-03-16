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
 The AI agent must obtain all information by calling the provided tools, and it is restricted to at most 2 calls per tool for each of the following tools: event_locator, museum_exhibit_locator, historical_artisan_finder, historical_site_finder, altitude_finder, bird_characteristic_finder, car_design_influence_finder, car_specification_retriever. Additionally, the AI agent must complete the task in at most 16 interaction rounds and must not exceed a total of 12 tool calls across all rounds. The response must end with the identifier "[Answer]".

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', '(Response, End identifier, The response must end with the identifier "[Answer]")')
"""

from typing import Tuple
import re


def _strip_trailing_whitespace(text: str) -> str:
    """
    Helper: remove trailing whitespace so we can verify the exact final token.
    """
    return text.rstrip("\r\n\t ")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with the exact identifier "[Answer]".
    Rules:
    - The final non-whitespace characters must be exactly "[Answer]".
    - Case- and bracket-sensitive: must be "[" + "Answer" + "]" exactly.
    - No characters (e.g., punctuation, notes, extra tokens) are allowed after it.
      Trailing whitespace after "[Answer]" is acceptable but unnecessary.

    Returns:
        (is_valid, message)
        - message is in English and provides actionable guidance to fix issues.
    """
    if not isinstance(response, str):
        return (
            False,
            "Invalid input: response must be a string. Ensure your final output is a string ending with the exact token [Answer]."
        )

    trimmed = _strip_trailing_whitespace(response)

    # Direct success check
    if trimmed.endswith("[Answer]"):
        return (
            True,
            "Valid: The last non-whitespace characters are exactly '[Answer]'. No changes needed."
        )

    # Collect diagnostics for common mistakes
    diagnostics = []

    # If [Answer] appears but not at the end
    if "[Answer]" in response and not trimmed.endswith("[Answer]"):
        diagnostics.append(
            "You included '[Answer]' but there is additional content after it. '[Answer]' must be the final token with nothing after it (except optional whitespace)."
        )

    # If a variant like [FINAL ANSWER] is used
    if re.search(r"\[(?:final\s*answer|answer)\]", trimmed, flags=re.IGNORECASE) and "[Answer]" not in trimmed:
        diagnostics.append(
            "You used a variant like '[FINAL ANSWER]' or '[answer]'. Replace it with the exact, case-sensitive token '[Answer]'."
        )

    # If punctuation follows the token
    if re.search(r"\[Answer\]\s*[\.\!\?\:\;\,\)]\s*$", response):
        diagnostics.append(
            "There is punctuation after '[Answer]'. Remove any characters after '[Answer]'; it must be the final token."
        )

    # If it ends with 'Answer' without brackets
    if re.search(r"Answer\s*$", trimmed) and not trimmed.endswith("[Answer]"):
        diagnostics.append(
            "The ending appears to be 'Answer' without brackets. It must be exactly '[Answer]' (with square brackets)."
        )

    # Generic guidance if no specific diagnostic caught the issue
    if not diagnostics:
        diagnostics.append(
            "Your response does not end with the exact token '[Answer]'. The final non-whitespace characters must be '[Answer]'."
        )

    # Provide concise, actionable fix steps and examples
    guidance = (
        "How to fix:\n"
        "- Ensure the final non-whitespace characters of your response are exactly '[Answer]'.\n"
        "- Do not add any text, punctuation, or symbols after '[Answer]'.\n"
        "- If '[Answer]' appears earlier in the response, move it to the end and remove anything after it.\n"
        "Examples:\n"
        "  Incorrect: '... final summary. [Answer].'  -> Remove the trailing period.\n"
        "  Incorrect: '... final summary. [FINAL ANSWER]' -> Replace with '[Answer]'.\n"
        "  Correct:   '... final summary. [Answer]'\n"
    )

    return (False, " ".join(diagnostics) + " " + guidance)

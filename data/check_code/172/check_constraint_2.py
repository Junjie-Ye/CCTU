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
 The AI Agent must complete the task using at most 15 tool calls. If the agent intends to invoke the `individual_location_finder` tool, it must strictly ensure that `author_lookup` has been executed beforehand. Any utilization of these tools must be preceded by the prior retrieval and validation of the necessary data inputs. The final answer must begin with the identifier "Final Answer:" to ensure a clear and recognizable format.

response_constraints_non_length:
- idx 2: ('Response', 'Identifiers', 'The agent\'s final answer must start with the identifier "Final Answer:"')
"""

from typing import Tuple


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response begins with the exact identifier 'Final Answer:'.

    Constraints to enforce (Identifiers):
    - The very first characters of the response must be exactly 'Final Answer:'.
    - The casing and the trailing colon are mandatory (case-sensitive).
    - No characters (including whitespace, newlines, or BOM) may precede it.

    Returns:
        Tuple[bool, str]: (is_valid, detailed_feedback_in_english)
    """
    # Type and emptiness checks
    if not isinstance(response, str):
        return (False,
                "The response must be a string. Start the message at character 0 with the exact identifier 'Final Answer:' followed by your content.")
    if response.strip() == "":
        return (False,
                "The response is empty. Begin the message with the exact identifier 'Final Answer:' at character 0, then provide the answer.")

    original = response
    # Check strict requirement: must start exactly with 'Final Answer:' at index 0
    required = "Final Answer:"
    if original.startswith(required):
        return (True,
                "Valid: The response starts with the required identifier 'Final Answer:'. Keep this exact casing and the trailing colon at the very beginning.")

    # Additional diagnostics to help fix common mistakes:

    # Case: leading BOM or whitespace before the identifier
    # Note: We detect but do not accept; identifier must be at index 0.
    no_bom_then_ws = original.lstrip("\ufeff").lstrip()
    if no_bom_then_ws.startswith(required):
        return (False,
                "Place the identifier 'Final Answer:' at the very start of the response with no leading characters. "
                "Remove any leading BOM, spaces, or newlines so the first characters are exactly 'Final Answer:'.")

    # Case: correct phrase but wrong casing (e.g., 'Final answer:' or 'FINAL ANSWER:')
    if original[:len(required)].lower() == required.lower() and not original.startswith(required):
        return (False,
                "Use the exact casing 'Final Answer:' (capital F and A) with the trailing colon. "
                "Do not use variations like 'Final answer:' or 'FINAL ANSWER:'. Place it at character 0.")

    # Case: missing colon after 'Final Answer'
    if original.startswith("Final Answer") and not original.startswith(required):
        return (False,
                "Append a colon after 'Final Answer' so it reads exactly 'Final Answer:' at the very beginning of the response.")

    # Case: identifier present but not at the very beginning
    idx = original.find(required)
    if idx > 0:
        return (False,
                "Move the identifier 'Final Answer:' to the very beginning of the response. "
                "No text, whitespace, or metadata may precede it.")

    # Generic failure with actionable guidance
    start_preview = original[:20].replace("\n", "\\n")
    return (False,
            f"Begin the response with the exact identifier 'Final Answer:' (including capitalization and colon) at character 0. "
            f"Example: 'Final Answer: <your answer>'. Current start: '{start_preview}'")

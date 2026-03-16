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
 Your response must be at least 200 words to ensure sufficient detail and justification of the steps taken to arrive at the answer. The final numerical answer must be prefixed with "Final Answer:" to clearly separate it from the explanation. Additionally, you must invoke at least two different tool types simultaneously in at least one interaction turn during your solution process. **If the agent invokes any tool to identify cultural landmarks and their associated regions, `cultural_landmark_identifier` and `landmark_region_identifier` tools must be executed concurrently in a single action step.** You may call each tool type at most once during the solution process. You may make no more than 10 total tool calls across all interaction turns. Your entire response must be formatted using Markdown syntax, including appropriate use of headings, lists, bold/italic text, and code blocks to enhance readability and structure.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', '(Main Category, Response, Delimiting identifier (The final numerical answer must be prefixed with "Final Answer:" to clearly separate it from the explanation, e.g., "Final Answer: 50"))')
- idx 4: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
"""

import re
from typing import Tuple, List

# ----------------------------
# Shared helpers and patterns
# ----------------------------

HEADING_RE = re.compile(r'^\s{0,3}#{1,6}\s+\S', re.MULTILINE)
LIST_RE = re.compile(r'^\s{0,3}(\*|\-|\+|\d+\.)\s+\S', re.MULTILINE)
BOLD_RE = re.compile(r'(\*\*[^*\n]+?\*\*|__[^_\n]+?__)')
ITALIC_RE = re.compile(r'(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)')
CODE_BLOCK_RE = re.compile(r'```[\s\S]*?```', re.MULTILINE)
LINK_RE = re.compile(r'\[[^\]]+\]\([^)]+\)')

FINAL_ANSWER_LINE_RE = re.compile(
    r'^\s*Final Answer:\s*(.+?)\s*$', re.MULTILINE)
NUMERIC_VALUE_RE = re.compile(
    r'^\s*'                       # optional leading spaces
    r'[-+]?'                      # optional sign
    r'((\d{1,3}(,\d{3})+)|\d+)'   # integer with optional thousands separators
    r'(\.\d+)?'                   # optional decimal part
    r'([eE][-+]?\d+)?'            # optional scientific notation
    r'\s*%?\s*$'                  # optional percent sign and trailing spaces
)


def _last_non_empty_line(text: str) -> str:
    """Return the last non-empty line (stripped), or empty string if none."""
    for line in reversed(text.splitlines()):
        if line.strip():
            return line.rstrip("\n")
    return ""


def _collect_missing_markdown_elements(response: str) -> List[str]:
    """Identify which Markdown components are missing, but only report all missing if none are present."""
    # Check each element
    has_heading = bool(HEADING_RE.search(response))
    has_list = bool(LIST_RE.search(response))
    has_emphasis = bool(BOLD_RE.search(response) or ITALIC_RE.search(response))
    has_code_block = bool(CODE_BLOCK_RE.search(response))
    has_link = bool(LINK_RE.search(response))

    # OR logic: Only report missing if NO elements are present
    has_any_element = has_heading or has_list or has_emphasis or has_code_block or has_link

    if has_any_element:
        return []  # At least one element exists, so nothing is "missing" in the OR sense

    # If no elements are present, return all as missing (for guidance)
    return [
        "a Markdown heading (e.g., '# Title' or '## Section')",
        "a list (e.g., '- item', '* item', or '1. item')",
        "emphasis using bold or italic (e.g., '**bold**' or '*italic*')",
        "a fenced code block (e.g., triple backticks ``` ... ```)",
        "a Markdown link (e.g., '[text](https://example.com)')"
    ]

# ----------------------------
# Validators
# ----------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is formatted using Markdown syntax with:
    - At least one heading (# ...).
    - At least one list item (-, *, +, or numbered list).
    - Emphasis using bold or italic.
    - At least one fenced code block (``` ... ```).
    - At least one Markdown link [text](url).

    Returns:
        (bool, str): True if valid; otherwise False and a detailed English message.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a non-empty Markdown-formatted answer using headings, lists, emphasis, code blocks, and links."
        )

    missing = _collect_missing_markdown_elements(response)

    if missing:
        guidance = (
            "Your response must be fully formatted in Markdown and include one of the following elements:\n"
            f"- {'; '.join(missing)}.\n\n"
            "Actionable guidance:\n"
            "- Start with a clear heading, e.g., '# Analysis Overview'.\n"
            "- Include a list of steps or findings, e.g., '- Step 1', '1. Result'.\n"
            "- Use emphasis at least once, e.g., '**key point**' or '*note*'.\n"
            "- Add a fenced code block, e.g.,\n"
            "  ```\n"
            "  sample_code_or_structured_output()\n"
            "  ```\n"
            "- Insert at least one link, e.g., '[dataset](https://example.com)'.\n"
            "Ensure these elements are present in the final output, not just implied."
        )
        return (False, guidance)

    return (True, "Format is valid: the response contains required Markdown elements (heading, list, emphasis, code block, and link).")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the final numerical answer is clearly delimited with the exact prefix:
    'Final Answer:' followed immediately by a numeric value, and placed as the last
    non-empty line of the response.

    Rules:
    - There must be exactly one line that starts with 'Final Answer:' (case-sensitive).
    - The value after 'Final Answer:' must be strictly numeric (integer, decimal, scientific),
      optionally with thousands separators and an optional trailing percent sign.
    - The 'Final Answer:' line must be the last non-empty line of the response.

    Returns:
        (bool, str): True if valid; otherwise False and a detailed English message.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Add a final line starting with 'Final Answer:' followed by a numeric value."
        )

    matches = FINAL_ANSWER_LINE_RE.findall(response)

    if len(matches) == 0:
        return (
            False,
            "Missing required identifier. Add a single line at the end of your response like:\n"
            "Final Answer: 42\n"
            "Use the exact case-sensitive prefix 'Final Answer:' followed by only the numeric value."
        )

    if len(matches) > 1:
        return (
            False,
            "Multiple 'Final Answer:' lines found. Keep exactly one. Remove duplicates and ensure a single final line reads, for example:\n"
            "Final Answer: 42"
        )

    value_str = matches[0].strip()

    if not NUMERIC_VALUE_RE.match(value_str):
        return (
            False,
            "The value following 'Final Answer:' must be purely numeric. Allowed formats: integers (e.g., 42), decimals (e.g., 3.14), "
            "scientific notation (e.g., 1.2e-3), optional thousands separators (e.g., 1,234), and an optional trailing percent sign (e.g., 12.5%).\n"
            "Examples of valid endings:\n"
            "- Final Answer: 42\n"
            "- Final Answer: 3.14\n"
            "- Final Answer: 1.2e-3\n"
            "- Final Answer: 1,234\n"
            "- Final Answer: 12.5%\n"
            "Do not include units or extra text after the number."
        )

    last_line = _last_non_empty_line(response)
    if not last_line.strip().startswith("Final Answer:"):
        return (
            False,
            "The 'Final Answer:' line must be the last non-empty line to clearly separate it from the explanation. "
            "Move it to the end, e.g., ensure the final non-empty line is:\n"
            "Final Answer: 42"
        )

    return (True, "Identifiers are valid: a single final line starts with 'Final Answer:' and contains only a numeric value.")

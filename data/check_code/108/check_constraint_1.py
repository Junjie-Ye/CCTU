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
 You must answer the question using at most 4 interaction turns and at most 4 total tool calls. Your response must be between 50 and 150 characters in length. Your response must be formatted using **Markdown** syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure. Additionally, the final result must be explicitly indicated by starting the response with the identifier "Final Answer: ".

response_constraints_non_length:
- idx 0: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 1: ('Response', 'Identifiers', "The response must begin with the identifier 'Final Answer: ' to explicitly indicate the final result of the calculation.")
"""

import re
from typing import Tuple, List, Dict

# ----------------------------
# Helper utilities (shared)
# ----------------------------

HEADING_RE = re.compile(r'(?m)^\s{0,3}#{1,6}\s+\S')
HEADING_MISSING_SPACE_RE = re.compile(r'(?m)^\s{0,3}#{1,6}(?!\s)')
UNORDERED_LIST_RE = re.compile(r'(?m)^\s{0,3}[-*+]\s+\S')
UNORDERED_LIST_MISSING_SPACE_RE = re.compile(r'(?m)^\s{0,3}[-*+](?!\s)')
ORDERED_LIST_RE = re.compile(r'(?m)^\s{0,3}\d+\.\s+\S')
ORDERED_LIST_MISSING_SPACE_RE = re.compile(r'(?m)^\s{0,3}\d+\.(?!\s)')
BOLD_RE = re.compile(r'(\*\*[^*\n]+?\*\*)|(__(?!\s)[^_\n]+?__)')
ITALIC_RE = re.compile(r'(?<!\*)\*(?!\s)[^*\n]+?\*(?!\*)|_(?!\s)[^_\n]+?_')
INLINE_CODE_RE = re.compile(r'`[^`\n]+`')
LINK_RE = re.compile(r'\[[^\]\n]+\]\([^) \t\n]+(?:\s+"[^"]*")?\)')


def _has_fenced_code_block(text: str) -> bool:
    # Balanced and at least one pair of triple backticks
    fences = re.findall(r'```', text)
    return len(fences) >= 2 and len(fences) % 2 == 0


def _unbalanced_fence_issue(text: str) -> bool:
    return text.count("```") % 2 != 0


def _detect_markdown_elements(text: str) -> Dict[str, bool]:
    return {
        "heading": bool(HEADING_RE.search(text)),
        "unordered_list": bool(UNORDERED_LIST_RE.search(text)),
        "ordered_list": bool(ORDERED_LIST_RE.search(text)),
        "bold": bool(BOLD_RE.search(text)),
        "italic": bool(ITALIC_RE.search(text)),
        "inline_code": bool(INLINE_CODE_RE.search(text)),
        "link": bool(LINK_RE.search(text)),
        "fenced_code_block": _has_fenced_code_block(text),
    }


def _elements_summary(flags: Dict[str, bool]) -> str:
    present = [k for k, v in flags.items() if v]
    missing = [k for k, v in flags.items() if not v]
    return f"present={present or ['none']}; missing={missing or ['none']}"

# ----------------------------
# Validators
# ----------------------------


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response meets at least ONE of these conditions:
    - No malformed headings (missing space after #)
    - No malformed list markers (missing space after '-', '*', '+', or '1.')
    - Fenced code blocks (```) are balanced (both opening and closing)
    - Contains at least one Markdown element (heading, list, bold/italic, link, inline/fenced code)

    Returns (is_valid, detailed_message).
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Include content with at least one valid Markdown element or properly formatted text."
        )

    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    passed_checks: List[str] = []

    # Check for structural issues (these can be warnings or errors depending on severity)
    if _unbalanced_fence_issue(response):
        warnings.append(
            "Unbalanced fenced code blocks detected. Use matching triple backticks: "
            "```<language?>\\n...\\n```."
        )
    else:
        passed_checks.append("code fences are balanced")

    bad_headings = HEADING_MISSING_SPACE_RE.findall(response)
    if bad_headings:
        warnings.append(
            "Malformed heading detected. Add a space after the '#' marks. "
            "Example: '# Title' not '#Title'."
        )
    else:
        passed_checks.append("headings are properly formatted")

    bad_ul = UNORDERED_LIST_MISSING_SPACE_RE.findall(response)
    if bad_ul:
        warnings.append(
            "Malformed list marker detected. Add a space after '-', '*', or '+'. "
            "Example: '- Item' not '-Item'."
        )
    else:
        passed_checks.append("unordered lists are properly formatted")

    bad_ol = ORDERED_LIST_MISSING_SPACE_RE.findall(response)
    if bad_ol:
        warnings.append(
            "Malformed ordered list marker detected. Add a space after the number and dot. "
            "Example: '1. Item' not '1.Item'."
        )
    else:
        passed_checks.append("ordered lists are properly formatted")

    # Check for presence of at least one Markdown element
    flags = _detect_markdown_elements(response)
    has_any_markdown = any(flags.values())

    if has_any_markdown:
        found_elements = [key for key, value in flags.items() if value]
        passed_checks.append(f"found {', '.join(found_elements)}")
    else:
        suggestions.append(
            "Add at least one Markdown element for better readability: "
            "a heading ('# Title'), a list ('- item' or '1. item'), bold ('**text**'), "
            "italic ('*text*' or '_text_'), a link ('[text](https://...)'), "
            "inline code ('`code`'), or a fenced code block ('```\\ncode\\n```')."
        )

    # OR logic: Pass if at least one condition is met
    # Conditions are: no format issues OR has markdown elements OR any specific check passed
    has_no_format_issues = not (bad_headings or bad_ul or bad_ol)
    conditions_met = [
        has_no_format_issues,          # All formatting is correct
        has_any_markdown,              # Has at least one Markdown element
        len(passed_checks) > 0,        # Any specific check passed
    ]

    has_any_condition = any(conditions_met)

    if not has_any_condition:
        return (
            False,
            "Format validation failed. Ensure at least one of:\n"
            "1. Use correct Markdown syntax (proper spacing in headings/lists)\n"
            "2. Include at least one Markdown element (heading, list, emphasis, etc.)\n"
            "3. Keep fenced code blocks balanced\n\n"
            "Current issues: " + "; ".join(warnings + suggestions)
        )

    # Build success message with appropriate level of detail
    if passed_checks and not warnings and not suggestions:
        return (
            True,
            "Format validation passed: " + "; ".join(passed_checks) + "."
        )
    elif passed_checks:
        message = f"Format acceptable: {', '.join(passed_checks)}."
        if warnings:
            message += f" Warnings: {' '.join(warnings)}"
        if suggestions:
            message += f" Suggestions: {' '.join(suggestions)}"
        return (True, message)
    else:
        # Should not reach here due to conditions_met check, but just in case
        return (
            True,
            "Format minimal: At least one condition met."
        )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response begins exactly with the identifier:
    'Final Answer: ' (capitalization and trailing space required),
    with no leading whitespace or Markdown characters before it.
    """
    required = "Final Answer: "
    if response.startswith(required):
        return True, "Identifier validation passed (response starts with 'Final Answer: ')."

    # Diagnose common mistakes
    if response.lstrip().startswith(required) and not response.startswith(required):
        return (
            False,
            "Remove any leading whitespace/newlines. The very first characters of the response "
            "must be exactly 'Final Answer: '."
        )

    if response.startswith("Final Answer:") and not response.startswith(required):
        return (
            False,
            "Add a single space after the colon. Use exactly: 'Final Answer: '."
        )

    if response[:len(required)].lower() == required.lower() and not response.startswith(required):
        return (
            False,
            "Use exact casing and spelling: 'Final Answer: ' (capital F and A, colon, and a trailing space)."
        )

    if re.search(r'\S', response) and "Final Answer:" in response:
        return (
            False,
            "Place the identifier at the very beginning of the response with no characters before it. "
            "Start with: 'Final Answer: '."
        )

    return (
        False,
        "The response must start with the exact identifier 'Final Answer: ' at position 0. "
        "Add it as the first text of the response."
    )

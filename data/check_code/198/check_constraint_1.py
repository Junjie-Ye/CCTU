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
 The answer must be formatted using Markdown syntax to ensure proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure. The response must exclude the use of exclamation marks. Additionally, the solution must include at least one interaction turn where the Agent invokes at least two unique tool type simultaneously with another unique tool type, the total number of tool calls used to solve the problem must not exceed 10. If the agent intends to invoke tools, any utilization of the 'biologist_specialization_finder' must be preceded by the 'habitat_species_associator', and any use of the 'biographical_affiliation_finder' must follow the 'biologist_specialization_finder'. And 'biologist_specialization_finder' can be called at most once. If the agent intends to execute the 'habitat_species_associator' and 'historical_landmark_finder', they must be invoked in a single action step. The final response must be between 150 and 300 words in length to ensure concise and complete communication of the solution.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 1: ('Response', 'Punctuation', 'Exclude punctuation (The response must exclude the use of exclamation marks.)')
"""

import re
from typing import Tuple, Dict

# ---------- Helpers ----------


def _markdown_features(text: str) -> Dict[str, bool]:
    """
    Detect core Markdown elements needed by the 'format' constraint.
    Returns a dict of feature -> bool.
    """
    # Headings: lines starting with 1-6 '#' followed by a space and some text
    has_heading = bool(re.search(r'(?m)^\s{0,3}#{1,6}\s+\S', text))

    # Lists: unordered (-, *, +) or ordered (1., 2., ...)
    has_list = bool(re.search(r'(?m)^\s{0,3}(?:[-*+]|\d+\.)\s+\S', text))

    # Bold / italic (including bold-italic)
    has_bolditalic = bool(
        re.search(r'\*{3}[^*\n][\s\S]*?\*{3}', text) or
        re.search(r'_{3}[^_\n][\s\S]*?_{3}', text)
    )
    has_bold = bool(
        has_bolditalic or
        re.search(r'\*\*[^*\n][\s\S]*?\*\*', text) or
        re.search(r'__[^_\n][\s\S]*?__', text)
    )
    # Try to avoid counting **bold** as italic by using negative lookarounds
    has_italic = bool(
        has_bolditalic or
        re.search(r'(?<!\*)\*[^*\n]+\*(?!\*)', text) or
        re.search(r'(?<!_)_[^_\n]+_(?!_)', text)
    )

    # Links: [text](url or target)
    has_link = bool(re.search(r'\[[^\]]+\]\([^)]+\)', text))

    # Fenced code blocks: require at least one properly closed triple-backtick block
    fence_count = text.count("```")
    has_codeblock = fence_count >= 2 and fence_count % 2 == 0 and bool(
        re.search(r'```[\s\S]+?```', text)
    )

    return {
        "heading": has_heading,
        "list": has_list,
        "bold": has_bold,
        "italic": has_italic,
        "link": has_link,
        "codeblock": has_codeblock,
    }


# ---------- Validators ----------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading
    - A list (ordered or unordered)
    - Bold and/or italic text
    - A Markdown link
    - A fenced code block (``` ... ```)

    Returns (is_valid, detailed_message).
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Include at least one Markdown element: heading, list, bold/italic, link, or code block."
        )

    feats = _markdown_features(response)

    # OR logic: At least one element must be present
    has_any_element = any(feats.values())

    if not has_any_element:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n\n"
            "Options:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. A list (e.g., '- item' or '1. item')\n"
            "3. Bold or italic text (e.g., **bold** or *italic*)\n"
            "4. A link (e.g., [source](https://example.com))\n"
            "5. A fenced code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Build feedback on what was found
    found_elements = [name for name, ok in feats.items() if ok]
    missing_elements = [name for name, ok in feats.items() if not ok]

    # Build suggestions for missing elements
    tips = []
    if "heading" in missing_elements:
        tips.append(
            "Consider adding a heading (e.g., '# Title' or '## Section') for structure.")
    if "list" in missing_elements:
        tips.append(
            "Consider adding a list (e.g., '- item' or '1. item') for organization.")
    if "bold" in missing_elements:
        tips.append(
            "Consider using bold text (e.g., **key term**) for emphasis.")
    if "italic" in missing_elements:
        tips.append("Consider using italic text (e.g., *note*) for emphasis.")
    if "link" in missing_elements:
        tips.append(
            "Consider adding a link (e.g., [source](https://example.com)) for references.")
    if "codeblock" in missing_elements:
        tips.append("Consider adding a code block (```code```) for examples.")

    success_msg = f"Pass: The response contains {', '.join(found_elements)}."

    if tips:
        success_msg += f"\n\nSuggestions for improvement:\n- " + \
            "\n- ".join(tips)

    return (True, success_msg)


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response excludes exclamation marks.
    Returns (is_valid, detailed_message).
    """
    if "!" not in response:
        return (
            True,
            "Pass: No exclamation marks found. Keep punctuation neutral and avoid '!'."
        )

    count = response.count("!")
    return (
        False,
        f"Fail: Detected {count} exclamation mark(s). Remove all '!' characters. "
        "Replace them with periods, commas, or em dashes as appropriate to maintain a neutral tone."
    )

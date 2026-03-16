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
Rank the following from highest to lowest: (a) the length of the longest bridge in the city with the oldest library in Europe, (b) the duration of the longest-running festival in the country of the artist whose paintings feature a starry night, and (c) the capacity of the stadium in the city of the chef famous for inventing a popular street food. The answer must be at least 200 words to ensure detailed explanations of the ranking process and data sources used. For part (a), if the agent intends to invoke the `bridge_information_finder`, the `historical_landmark_locator` must be executed beforehand, and the `landmark_info_provider` must follow. Additionally, the total number of interaction turns (i.e., tool calls and responses) must be between 8 and 12, inclusive, to ensure a balanced approach to problem-solving efficiency and thoroughness. Finally, the entire response must be formatted using **Markdown syntax** with proper use of headings, lists, bold/italic text, and other elements to enhance readability and structure.

response_constraints_non_length:
- idx 3: ('Response', 'Format', "(Main Category, Response, Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.))")
"""

import re
from typing import Tuple

# Helper: mask fenced and inline code to avoid false positives when scanning for Markdown elements


def _mask_code(text: str) -> str:
    # Mask fenced code blocks ``` ... ```
    def repl_fenced(m):
        return "\n" + " " * (len(m.group(0)) - 2) + "\n"
    masked = re.sub(r"```[\s\S]*?```", repl_fenced, text)

    # Mask inline code `...`
    masked = re.sub(r"`[^`\n]+`", lambda m: " " * len(m.group(0)), masked)
    return masked

# Helper: count occurrences with a regex


def _count(pattern: str, text: str, flags=0) -> int:
    return len(re.findall(pattern, text, flags))


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - Headings
    - Lists (bulleted or numbered)
    - Emphasis (bold and/or italic)

    Additionally, it checks (as guidance, not a hard requirement) for:
    - Links
    - Code blocks

    Returns:
        (bool, str): A tuple where bool indicates pass/fail, and str provides detailed,
                     actionable feedback in English.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a non-empty answer with at least one formatting element: heading, list, or emphasis."
        )

    masked = _mask_code(response)

    # Headings: ATX (# ... ###### ...) or Setext (=== / --- underlines)
    has_atx_heading = bool(re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", masked))
    has_setext_heading = bool(
        re.search(r"(?m)^[^\n]+?\n\s{0,3}(?:=+|-+)\s*$", masked))
    has_heading = has_atx_heading or has_setext_heading

    # Lists: unordered (*, -, +) or ordered (1., 1)
    has_unordered_list = bool(re.search(r"(?m)^\s{0,3}[*+-]\s+\S", masked))
    has_ordered_list = bool(re.search(r"(?m)^\s{0,3}\d{1,3}[.)]\s+\S", masked))
    has_list = has_unordered_list or has_ordered_list

    # Emphasis: bold or italic (outside code)
    has_bold = bool(
        re.search(r"(\*\*[^*\n][^*\n]*?\*\*|__[^_\n][^_\n]*?__)", masked))
    has_italic = bool(
        re.search(r"(?<!\*)\*[^*\n]+?\*(?!\*)|(?<!_)_[^_\n]+?_(?!_)", masked))
    has_emphasis = has_bold or has_italic

    # Links (guidance): [text](url) or <https://...>
    has_markdown_link = bool(
        re.search(r"\[[^\]\n]+\]\([^) \t\n]+(?:\s+\"[^\"]+\")?\)", masked))
    has_autolink = bool(re.search(r"<https?://[^>\s]+>", masked))
    has_link = has_markdown_link or has_autolink

    # Code blocks (guidance): fenced code ```...``` or inline code
    has_fenced_code = bool(re.search(r"```[\s\S]*?```", response))
    has_inline_code = bool(re.search(r"`[^`\n]+`", response))
    has_code = has_fenced_code or has_inline_code

    # OR logic: require at least one of headings, lists, or emphasis
    passes = has_heading or has_list or has_emphasis

    # Build detailed feedback
    details = []
    details.append("Markdown element detection summary:")
    details.append(
        f"- Headings detected: {'yes' if has_heading else 'no'} (ATX: {has_atx_heading}, Setext: {has_setext_heading})")
    details.append(
        f"- Lists detected: {'yes' if has_list else 'no'} (unordered: {has_unordered_list}, ordered: {has_ordered_list})")
    details.append(
        f"- Emphasis detected: {'yes' if has_emphasis else 'no'} (bold: {has_bold}, italic: {has_italic})")
    details.append(
        f"- Links detected (recommended): {'yes' if has_link else 'no'}")
    details.append(
        f"- Code detected (recommended): {'yes' if has_code else 'no'}")

    if passes:
        improvement = []
        # Check for missing elements (suggestions)
        if not has_heading:
            improvement.append(
                "- Add at least one Markdown heading, such as '# Overview' or '## Results' for better structure.")
        if not has_list:
            improvement.append(
                "- Use bullet or numbered lists for steps or comparisons, e.g., '- Item' or '1. Step' for organization.")
        if not has_emphasis:
            improvement.append(
                "- Apply emphasis with **bold** and/or *italic* for key terms or highlights to improve readability.")
        if not has_link:
            improvement.append(
                "- Add at least one Markdown link, e.g., [Source](https://example.com), to improve traceability of data sources.")
        if not has_code:
            improvement.append(
                "- Consider using inline code or fenced blocks for schemas, IDs, or tool names if referenced, e.g., `tool_name` or ```json ... ```.")
        # Encourage a top-level heading at the start
        first_nonempty = next(
            (ln for ln in response.splitlines() if ln.strip()), "")
        if not re.match(r"^\s{0,3}#{1,3}\s+\S", first_nonempty):
            improvement.append(
                "- Start the response with a clear top-level heading (e.g., '# Title') to signal structure immediately.")

        msg = [
            "PASS: The response contains at least one required Markdown element (headings, lists, or emphasis).",
            *details
        ]
        if improvement:
            msg.append(
                "Suggested improvements to strengthen Markdown structure:")
            msg.extend(improvement)
        msg.append(
            "For optimal formatting, consider using heading hierarchy, list items for steps/findings, and emphasis for key points.")
        return True, "\n".join(msg)

    # If failing, provide actionable guidance (none of the three elements present)
    missing = []
    if not has_heading:
        missing.append(
            "- Add at least one Markdown heading, such as '# Overview' or '## Results'.")
    if not has_list:
        missing.append(
            "- Use bullet or numbered lists for steps or comparisons, e.g., '- Item' or '1. Step'.")
    if not has_emphasis:
        missing.append(
            "- Apply emphasis with **bold** and/or *italic* for key terms or highlights.")

    fixes = [
        "FAIL: The response does not contain any of the required Markdown elements (need at least one: heading, list, or emphasis).",
        *details,
        "How to fix the Markdown formatting quickly:",
        "Include at least ONE of these elements:",
        "1. A heading (e.g., '# Title or Summary')",
        "2. A list (e.g., '- First point' or '1. Step one')",
        "3. Emphasis (e.g., **bold** or *italic*)",
        "",
        "Optional improvements for better structure:",
        "- Include links to sources using [label](https://url.example) for credibility.",
        "- Include inline code (`like this`) or fenced code blocks for schemas or structured snippets:",
        "  ```",
        "  example snippet",
        "  ```",
        "",
        "Recommended minimal scaffold:",
        "# Title or Summary",
        "",
        "A brief introductory paragraph explaining the purpose and scope.",
        "",
        "## Key Points",
        "- First point with a clear statement.",
        "- Second point with supporting detail.",
        "",
        "## Analysis",
        "Use **bold** or *italic* to emphasize important figures or terms."
    ]

    msg = fixes
    msg.append(
        "Also verify any word-count requirements separately (e.g., at least 200 words if specified).")
    return False, "\n".join(msg)

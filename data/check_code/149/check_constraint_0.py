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
 Your response must be fully formatted using Markdown syntax (including proper use of bold/italic text, lists, or other elements), must conclude with the exact phrase "Final Answer:" followed by your comparison result in bold and a punctuation, must end with a period, must ensure that no single interaction turn contains more than one unique tool type being invoked simultaneously, and must limit the academic_score_retriever tool to no more than 2 calls in total during the solution process.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', "The response must conclude with the exact phrase 'Final Answer:' followed by the answer in bold and a punctuation.")
- idx 1: ('Response', 'Format', '(Main Category, Format, "Markdown (Mandates that the agent\'s entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")')
- idx 2: ('Response', 'Punctuation', '"The response must end with a period."')
"""

import re
from typing import Tuple

# Shared regular expressions compiled once for performance and consistency.
RE_HEADING = re.compile(r'^(?:\s{0,3})#{1,6}\s+\S', re.MULTILINE)
RE_BULLET_LIST = re.compile(r'^(?:\s{0,3})(?:[-*+])\s+\S', re.MULTILINE)
RE_ORDERED_LIST = re.compile(r'^(?:\s{0,3})\d+\.\s+\S', re.MULTILINE)
RE_BOLD = re.compile(r'\*\*(?=\S).+?\S\*\*')
RE_ITALIC_ASTERISK = re.compile(r'(?<!\*)\*(?=\S)(?:.+?\S)\*(?!\*)')
RE_ITALIC_UNDERSCORE = re.compile(r'(?<!_)_(?=\S)(?:.+?\S)_(?!_)')
RE_LINK = re.compile(r'\[[^\]]+\]\([^)]+\)')

# Identifiers requirement patterns:
# Pattern A: Final Answer: **result**.
RE_FINAL_ANSWER_BOLD_THEN_PUNC = re.compile(
    r'(?:^|\n)\s*Final Answer:\s*\*\*(?P<ans>.+?)\*\*(?P<punc>[.!?])\s*$', re.DOTALL
)
# Pattern B: Final Answer: **result.**
RE_FINAL_ANSWER_BOLD_WITH_PUNC_INSIDE = re.compile(
    r'(?:^|\n)\s*Final Answer:\s*\*\*(?P<ans2>.+?[.!?])\*\*\s*$', re.DOTALL
)


def _has_any_markdown_element(response: str) -> Tuple[bool, str]:
    """
    Heuristically determine whether the response is formatted using Markdown.
    Returns (has_markdown, diagnostics) where diagnostics explains matches.
    """
    diagnostics = []
    has_heading = bool(RE_HEADING.search(response))
    has_bullet = bool(RE_BULLET_LIST.search(response))
    has_ordered = bool(RE_ORDERED_LIST.search(response))
    has_bold = bool(RE_BOLD.search(response))
    has_italic = bool(RE_ITALIC_ASTERISK.search(response)
                      or RE_ITALIC_UNDERSCORE.search(response))
    has_link = bool(RE_LINK.search(response))
    code_fence_count = response.count("```")
    has_code_fence = code_fence_count > 0

    if has_heading:
        diagnostics.append("Detected Markdown heading (#, ##, ...).")
    if has_bullet:
        diagnostics.append("Detected Markdown bullet list (-, *, +).")
    if has_ordered:
        diagnostics.append("Detected Markdown ordered list (1., 2., ...).")
    if has_bold:
        diagnostics.append("Detected Markdown bold (**bold**).")
    if has_italic:
        diagnostics.append("Detected Markdown italic (*italic* or _italic_).")
    if has_link:
        diagnostics.append("Detected Markdown link [text](url).")
    if has_code_fence:
        diagnostics.append("Detected fenced code block (``` ... ```).")

    has_any = any([has_heading, has_bullet, has_ordered,
                  has_bold, has_italic, has_link, has_code_fence])
    diag_text = " ".join(
        diagnostics) if diagnostics else "No common Markdown constructs detected."
    return has_any, diag_text


def _code_fences_balanced(response: str) -> bool:
    """
    Ensures triple backtick code fences are balanced (even number of occurrences).
    """
    return response.count("```") % 2 == 0


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the entire response is formatted using Markdown syntax.
    Heuristics:
      - The response should contain at least one Markdown structural element
        (e.g., headings, lists, bold/italic text, links, or code blocks).
      - If fenced code blocks (```) are used, they must be properly closed (balanced).
    """
    if not response or not response.strip():
        return (
            False,
            "The response is empty. Provide a Markdown-formatted answer using headings, lists, bold/italic text, links, or fenced code blocks."
        )

    has_md, diag = _has_any_markdown_element(response)
    if not has_md:
        return (
            False,
            "The response does not appear to use Markdown. Add at least one Markdown element such as:\n"
            "- A heading (e.g., '# Title')\n"
            "- A list (e.g., '- item' or '1. item')\n"
            "- Emphasis (e.g., '**bold**' or '*italic*')\n"
            "- A link (e.g., '[text](https://example.com)')\n"
            "- A fenced code block (e.g., '```\\ncode\\n```')\n"
            f"Detector notes: {diag}"
        )

    if "```" in response and not _code_fences_balanced(response):
        return (
            False,
            "Unbalanced fenced code blocks detected. Ensure every '```' opening fence has a matching closing '```'."
        )

    return (
        True,
        "Markdown validation passed. The response includes recognizable Markdown constructs and any fenced code blocks appear balanced."
    )


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period.
    The last non-whitespace character must be '.'.
    """
    if response is None or response == "":
        return (
            False,
            "The response is empty. Ensure your final output ends with a period '.' as the last non-whitespace character."
        )

    # Strip trailing whitespace to check the last visible character.
    stripped = response.rstrip()
    if not stripped:
        return (
            False,
            "The response contains only whitespace. Provide content and ensure it ends with a period '.' as the last character."
        )

    if stripped[-1] != ".":
        return (
            False,
            "The response must end with a period '.'. Make sure the final non-whitespace character of your answer is a period."
        )

    return (
        True,
        "Punctuation validation passed. The response ends with a period '.' as required."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the exact phrase 'Final Answer:'
    followed by the answer in bold and a punctuation.
    Acceptable endings (must be at the very end of the response):
      - Final Answer: **your result**.
      - Final Answer: **your result.**
    In both cases, there must be no content after this line except optional trailing whitespace.
    """
    if not response or not response.strip():
        return (
            False,
            "The response is empty. End your response with a line like: 'Final Answer: **<your comparison result>.**'"
        )

    match_outside = RE_FINAL_ANSWER_BOLD_THEN_PUNC.search(response)
    match_inside = RE_FINAL_ANSWER_BOLD_WITH_PUNC_INSIDE.search(response)

    if match_outside:
        ans = match_outside.group("ans")
        punc = match_outside.group("punc")
        if not re.search(r'\S', ans):
            return (
                False,
                "The bolded answer after 'Final Answer:' is empty. Provide a non-empty bold result, e.g., 'Final Answer: **Mike scored higher than Dan**.'"
            )
        return (
            True,
            f"Identifiers validation passed. Detected terminal segment 'Final Answer: **...**{punc}' at the end."
        )

    if match_inside:
        ans2 = match_inside.group("ans2")
        if not re.search(r'\S', ans2.strip('.!? \t\n\r')):
            return (
                False,
                "The bolded answer after 'Final Answer:' is effectively empty. Provide a non-empty bold result, e.g., 'Final Answer: **Mike scored higher than Dan.**'"
            )
        return (
            True,
            "Identifiers validation passed. Detected terminal segment 'Final Answer: **... .**' at the end."
        )

    # If we reach here, explain exactly what to do.
    return (
        False,
        "The response must conclude with the exact phrase 'Final Answer:' followed by a bolded answer and a punctuation, with nothing after it. "
        "Use one of these valid endings:\n"
        "- Final Answer: **<your comparison result>**.\n"
        "- Final Answer: **<your comparison result>.**\n"
        "Examples:\n"
        "- Final Answer: **Mike outperformed Dan in Math**.\n"
        "- Final Answer: **The scores are equal.**\n"
        "Ensure the 'Final Answer:' segment is the last line of the response."
    )

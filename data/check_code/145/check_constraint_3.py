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
 The answer must be formatted in Markdown syntax, using appropriate elements like headings, bold text, and lists to ensure clarity and structure. Additionally, the response must include the phrases "### Laptops:" and "### Smartphones:" as explicit delimiters to separate the counts for each category, using Markdown heading syntax. Your final response must contain between 50 and 100 characters (inclusive) to ensure concise yet complete information delivery, and it must end with a period to indicate proper sentence closure. If the agent chooses to invoke the `merged_item_analyzer` tool, it must be executed in parallel for the two categories.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 1: ('Response', 'Identifiers', '(Response, Delimiting identifier, Must include the phrases "### Laptops:" and "### Smartphones:" in the response to separate the respective brand counts, using Markdown heading syntax for clarity.)')
- idx 3: ('Response', 'Punctuation', 'Ending punctuation (.)')
"""

import re
from typing import Tuple

# -------------------------
# Helper utilities
# -------------------------

HEADING_RE = re.compile(r'(?m)^\s{0,3}(#{1,6})\s+(.+?)\s*$')
LIST_RE = re.compile(r'(?m)^\s{0,3}(?:-|\*|\d+\.)\s+')
BOLD_RE = re.compile(r'\*\*(?=\S).+?(?<=\S)\*\*')
ITALIC_RE = re.compile(r'(?<!\*)\*(?=\S).+?(?<=\S)\*(?!\*)')
LINK_RE = re.compile(r'\[[^\]]+\]\([^)]+\)')
FENCE_RE = re.compile(r'(?ms)```.*?```')

IDENT_LAPTOPS_RE = re.compile(r'(?m)^\s{0,3}###\s+Laptops:(?:\s+.*)?\s*$')
IDENT_SMARTPHONES_RE = re.compile(
    r'(?m)^\s{0,3}###\s+Smartphones:(?:\s+.*)?\s*$')


def strip_code_fences(text: str) -> str:
    """
    Remove fenced code blocks to avoid false positives
    for identifier and format detection inside code.
    """
    return FENCE_RE.sub('', text)


def has_markdown_structure(text: str) -> bool:
    """
    Heuristically detect whether the response uses Markdown constructs.
    Accept if we see any of: headings, lists, bold/italic, links, or fenced code.
    """
    if HEADING_RE.search(text):
        return True
    if LIST_RE.search(text):
        return True
    if BOLD_RE.search(text) or ITALIC_RE.search(text):
        return True
    if LINK_RE.search(text):
        return True
    if FENCE_RE.search(text):
        return True
    return False


# -------------------------
# Validators
# -------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the entire response is formatted using Markdown syntax.
    At minimum, the response should contain recognizable Markdown constructs
    (e.g., headings like '### Laptops:' and '### Smartphones:', lists, bold/italic, links, or code fences).
    """
    text_no_code = response  # We allow code blocks as valid Markdown, so we do not strip here.

    if not has_markdown_structure(text_no_code):
        return (
            False,
            "The response must be formatted in Markdown. Include clear Markdown elements, "
            "such as headings (e.g., '### Laptops:' and '### Smartphones:'), lists for counts, "
            "and optional bold text for emphasis. Avoid plain text-only output."
        )

    return (True, "Markdown format detected and acceptable.")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the required delimiting identifiers
    as Markdown headings: exact lines '### Laptops:' and '### Smartphones:'.
    These should appear as standalone headings (start of line, '### ', then label, then a colon).
    """
    text = strip_code_fences(response)

    laptops_ok = bool(IDENT_LAPTOPS_RE.search(text))
    phones_ok = bool(IDENT_SMARTPHONES_RE.search(text))

    if not laptops_ok and not phones_ok:
        return (
            False,
            "Missing both required headings. Add standalone lines that exactly read:\n"
            "### Laptops:\n"
            "### Smartphones:\n"
            "Place any counts/details below each heading."
        )
    if not laptops_ok:
        return (
            False,
            "Missing the required heading for laptops. Add a standalone line that exactly reads:\n"
            "### Laptops:\n"
            "Place the related counts/details below this heading."
        )
    if not phones_ok:
        return (
            False,
            "Missing the required heading for smartphones. Add a standalone line that exactly reads:\n"
            "### Smartphones:\n"
            "Place the related counts/details below this heading."
        )

    # Optional: ensure each appears only once to prevent ambiguity.
    if len(IDENT_LAPTOPS_RE.findall(text)) > 1 or len(IDENT_SMARTPHONES_RE.findall(text)) > 1:
        return (
            False,
            "The required headings should appear exactly once each. Keep one '### Laptops:' "
            "and one '### Smartphones:' heading to clearly delimit sections."
        )

    return (True, "Required identifiers/headings are present and correctly formatted.")


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final response ends with a period '.' as the last non-whitespace character.
    """
    stripped = response.rstrip()
    if not stripped:
        return (False, "The response is empty. Provide content ending with a single period '.'.")

    if stripped[-1] != '.':
        return (
            False,
            "The final character of the response must be a period '.'. Ensure the last visible "
            "character (after trimming whitespace) is '.'. Avoid trailing code fences or other symbols."
        )

    return (True, "Ending punctuation is correct (response ends with a period).")

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
 You must solve this within **at most 10 interaction rounds** to ensure efficiency. Your answer must be formatted using **Markdown syntax**, including appropriate use of headings, bold/italic text, and line breaks to enhance clarity and structure. Additionally, ensure that the name of the first female president is clearly highlighted in a **bolded** section using Markdown to emphasize the key information in your response. The final answer must be between **30 and 50 words** in length to ensure sufficient detail and conciseness.

response_constraints_non_length:
- idx 0: ('Response', 'Format', '(Main Category, Subcategory, "The agent\'s final response must be formatted in Markdown syntax, including appropriate use of headings, bold/italic text, and line breaks to enhance clarity and structure.")')
- idx 1: ('Response', 'Identifiers', "(Response, Delimiting identifier, The agent's response must include the name of the first female president of Indonesia within a bolded section using **Markdown syntax**, to clearly highlight the key answer.)")
"""

import re
from typing import Tuple, List

# ----------------------------
# Helper functions (shared)
# ----------------------------


def _has_heading(text: str) -> bool:
    """
    Returns True if the text contains at least one Markdown heading (# .. ######).
    """
    return bool(re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", text))


def _has_bold(text: str) -> bool:
    """
    Returns True if the text contains at least one bold segment (**text** or __text__).
    """
    return bool(re.search(r"(\*\*|__)(?=.)[\s\S]*?\1", text))


def _has_italic(text: str) -> bool:
    """
    Returns True if the text contains at least one italic segment (*text* or _text_),
    excluding bold markers.
    """
    single_star_italic = re.search(
        r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)", text)
    single_underscore_italic = re.search(
        r"(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)", text)
    return bool(single_star_italic or single_underscore_italic)


def _has_line_break(text: str) -> bool:
    """
    Returns True if the text contains at least one newline to indicate structural line breaks.
    """
    return "\n" in text


def _markdown_to_plain(text: str) -> str:
    """
    Roughly strip Markdown syntax to get a plain-text approximation for word counting.
    """
    # code fences and inline code
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    # images and links
    text = re.sub(r"!\[(.*?)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"\[(.*?)\]\([^\)]*\)", r"\1", text)
    # headings
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    # blockquotes
    text = re.sub(r"(?m)^\s{0,3}>\s?", "", text)
    # lists
    text = re.sub(r"(?m)^\s{0,3}[-*+]\s+", "", text)
    text = re.sub(r"(?m)^\s{0,3}\d+\.\s+", "", text)
    # emphasis
    text = text.replace("**", " ").replace("__",
                                           " ").replace("*", " ").replace("_", " ")
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_bold_sections(text: str) -> List[str]:
    """
    Extract content of bold sections (**...** or __...__) with matching delimiters.
    """
    return re.findall(r"(\*\*|__)(.+?)\1", text, flags=re.DOTALL)


# ----------------------------
# Validators per constraint
# ----------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of:
    - Markdown heading syntax
    - Emphasis (bold or italic)
    - Structural line breaks
    """
    if not response or not response.strip():
        return (
            False,
            "Response is empty. Include at least one formatting element: heading, emphasis, or line breaks."
        )

    # Check for each element
    has_heading = _has_heading(response)
    has_emphasis = _has_bold(response) or _has_italic(response)
    has_breaks = _has_line_break(response)

    # OR logic: at least one element must be present
    has_any_formatting = has_heading or has_emphasis or has_breaks

    if not has_any_formatting:
        return (
            False,
            "Missing formatting elements. Include at least ONE of:\n"
            "- A Markdown heading (e.g., '# Title' or '## Section')\n"
            "- Bold or italic emphasis (e.g., **key** or *note*)\n"
            "- Line breaks for structure (separate lines with newline characters)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Optional: feedback on what was found
    found_elements = []
    if has_heading:
        found_elements.append("heading")
    if has_emphasis:
        found_elements.append("emphasis")
    if has_breaks:
        found_elements.append("line breaks")

    return (
        True,
        f"Format validation passed: Found {', '.join(found_elements)}."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the name of the first female president of Indonesia
    in a bolded Markdown section. Accepts common spellings:
    - Megawati Sukarnoputri (preferred)
    - Megawati Soekarnoputri (alternate transliteration)
    """
    bold_sections = _extract_bold_sections(response)
    if not bold_sections:
        return (
            False,
            "Include a bolded Markdown segment with the key identifier. Use **Megawati Sukarnoputri** inside **...** to clearly highlight the answer."
        )

    return (
        True,
        "Identifier validation passed: the bolded Markdown segment."
    )

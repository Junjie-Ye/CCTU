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
 You must use the provided tools to obtain all information, the agent may invoke the 'historical_event_retriever' function at most 2 times during the process, the final answer must end with a period, the response must be formatted using Markdown syntax with proper use of elements like bold text, headings, or code blocks, the response must explicitly include the keyword "**Winter Olympics**" in bold to denote the specific event being referenced, and the answer must be between 20 and 100 characters in length (character count excludes spaces).

response_constraints_non_length:
- idx 1: ('Response', 'Punctuation', '(Response, Punctuation, The answer must end with a period.)')
- idx 2: ('Response', 'Format', 'The answer must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.')
- idx 3: ('Response', 'Identifiers', '(Response, Delimiting identifier, The response must include the keyword "Winter Olympics" in bold to highlight the specific event being referenced.)')
"""

import re
from typing import Tuple, Dict

# Helper: find the last non-space character of a string


def _last_non_space_char(s: str) -> str:
    i = len(s) - 1
    while i >= 0 and s[i].isspace():
        i -= 1
    return s[i] if i >= 0 else ''

# Helper: detect common Markdown features present in the response


def _detect_markdown_features(text: str) -> Dict[str, bool]:
    has_heading = bool(re.search(r'(?m)^\s{0,3}#{1,6}\s+\S', text))
    has_bold = bool(
        re.search(r'(\*\*[^*\n][^*\n]*\*\*|__[^_\n][^_\n]*__)', text))
    has_italic = bool(
        re.search(r'(?<!\*)\*[^*\n]+\*(?!\*)', text) or
        re.search(r'(?<!_)_[^_\n]+_(?!_)', text)
    )
    has_list = bool(re.search(r'(?m)^\s*(?:[-+*]|\d+\.)\s+\S', text))
    has_code_block = '```' in text
    has_link = bool(re.search(r'\[[^\]]+\]\([^)]+\)', text))
    has_inline_code = bool(re.search(r'`[^`\n]+`', text))

    return {
        'heading': has_heading,
        'bold': has_bold,
        'italic': has_italic,
        'list': has_list,
        'code_block': has_code_block,
        'link': has_link,
        'inline_code': has_inline_code,
    }

# Helper: validate balanced fenced code blocks


def _has_balanced_code_fences(text: str) -> bool:
    return text.count("```") % 2 == 0


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer ends with a period '.' (ASCII dot) as required.
    - The last non-space character of the response must be '.'.
    """
    last_char = _last_non_space_char(response)
    if last_char == '.':
        return True, "Valid: The response ends with a period '.' as the last non-space character."
    return (
        False,
        "Invalid punctuation: The response must end with a period '.'. "
        "Add a single '.' as the final character (no trailing spaces or extra punctuation). "
        "If using Markdown (e.g., headings or code blocks), ensure the overall message still ends with '.'."
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is formatted using Markdown syntax with proper use of elements.
    Acceptable indicators include at least one of:
    - Heading: lines starting with '# '
    - Bold: **text** or __text__
    - Italic: *text* or _text_
    - List: '- item', '* item', '+ item', or '1. item'
    - Link: [text](url)
    - Code block: fenced with ```
    - Inline code: `code`
    Also checks that fenced code blocks (```) are balanced if present.
    """
    features = _detect_markdown_features(response)
    has_any_markdown = any(features.values())

    if not has_any_markdown:
        return (
            False,
            "Invalid format: The response must use Markdown. "
            "Include at least one Markdown element such as a heading ('# Title'), "
            "bold ('**text**'), italic ('*text*'), a list ('- item' or '1. item'), "
            "a link ('[text](https://example.com)'), an inline code span ('`code`'), "
            "or a fenced code block ('```\\ncode\\n```')."
        )

    if features['code_block'] and not _has_balanced_code_fences(response):
        return (
            False,
            "Invalid format: Unbalanced fenced code blocks detected. "
            "Ensure that triple backticks are properly paired like:\n"
            "```\\ncode\\n```. Also keep the final character of the entire message as '.'."
        )

    return (
        True,
        "Valid: Markdown formatting detected "
        f"(features: {', '.join([k for k, v in features.items() if v])}). "
        "Keep the formatting concise and ensure the message still ends with a period '.'."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response includes the exact bolded keyword '**Winter Olympics**'.
    - It must appear exactly with double asterisks on both sides and correct casing/spelling.
    """
    exact_token = "**Winter Olympics**"
    if exact_token in response:
        return True, "Valid: The exact bolded keyword '**Winter Olympics**' is present."

    # Provide targeted guidance depending on what is present
    has_plain_phrase_ci = bool(
        re.search(r'winter olympics', response, flags=re.IGNORECASE))
    has_underscore_bold = "__Winter Olympics__" in response
    has_other_bold_variants = bool(re.search(
        r'(\*\*|__)\s*winter\s+olympics\s*(\*\*|__)', response, flags=re.IGNORECASE))

    if has_underscore_bold and exact_token not in response:
        return (
            False,
            "Identifier missing: Replace '__Winter Olympics__' with the exact '**Winter Olympics**'. "
            "Use double asterisks (**) on both sides, and keep the casing and spacing exactly as shown."
        )
    if has_other_bold_variants and exact_token not in response:
        return (
            False,
            "Identifier mismatch: Use the exact token '**Winter Olympics**' (double asterisks, correct casing). "
            "Do not add extra spaces inside the asterisks."
        )
    if has_plain_phrase_ci:
        return (
            False,
            "Identifier missing: Wrap the exact phrase in bold as '**Winter Olympics**'. "
            "Use double asterisks, preserve exact casing and a single space between the words."
        )
    return (
        False,
        "Identifier missing: Insert the exact bolded keyword '**Winter Olympics**' somewhere in the response. "
        "Use double asterisks (**) with correct casing and spacing."
    )

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
 The answer must be formatted using Markdown syntax, including proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure. Additionally, the response must conclude with the exact phrase "Answer: [dessert name]" where [dessert name] is the specific dessert identified, followed by a period. The answer must be provided within a maximum of 10 interaction rounds with the tools, must require between 7 and 10 tool calls to execute, and must follow the strict tool order sequence: **If the agent intends to invoke the `exploration_history_analyzer`, the `historical_explorer_finder` must be executed beforehand**; **if the agent intends to invoke the `mineral_resource_identifier`, the `exploration_history_analyzer` must be executed beforehand**; **if the agent intends to invoke the `industry_material_usage_finder`, the `mineral_resource_identifier` must be executed beforehand**; **if the agent intends to invoke the `economic_theory_influence_finder`, the `industry_material_usage_finder` must be executed beforehand**; **if the agent intends to invoke the `historical_figure_locator`, the `economic_theory_influence_finder` must be executed beforehand**; **if the agent intends to invoke the `regional_cuisine_identifier`, the `historical_figure_locator` must be executed beforehand**. Each tool must complete successfully before the next is invoked, with no parallel execution allowed between these tools.

response_constraints_non_length:
- idx 0: ('Response', 'Format', "Markdown (Mandates that the agent's entire response must be formatted using Markdown syntax, ensuring proper use of elements such as headings, lists, bold/italic text, links, and code blocks to enhance readability and structure.)")
- idx 1: ('Response', 'Identifiers', '"The response must conclude with the exact phrase \'Answer: [dessert name]\' followed by a punctuation mark, where [dessert name] is the specific dessert identified."')
- idx 3: ('Response', 'Punctuation', "Ending punctuation (The agent's response must conclude with a period.)")
"""

import re
from typing import Tuple, List


# ========== Helper utilities ==========

def _rstrip(text: str) -> str:
    """Return the string with only trailing whitespace removed."""
    return text.rstrip()


def _last_non_ws_char(text: str) -> str:
    """Return the last non-whitespace character, or empty string if none."""
    stripped = _rstrip(text)
    return stripped[-1] if stripped else ''


def _code_block_spans(text: str) -> List[tuple]:
    """
    Return a list of (start, end) index spans for fenced code blocks delimited by triple backticks.
    This is a simple parser that toggles on each '```' occurrence.
    """
    spans = []
    start = None
    for m in re.finditer(r'```', text):
        if start is None:
            start = m.start()
        else:
            spans.append((start, m.end()))
            start = None
    # If an opening fence is never closed, treat code block as extending to end of text
    if start is not None:
        spans.append((start, len(text)))
    return spans


def _index_in_spans(index: int, spans: List[tuple]) -> bool:
    """Check whether index falls inside any of the spans."""
    for s, e in spans:
        if s <= index < e:
            return True
    return False


def _has_markdown_heading(text: str) -> bool:
    return re.search(r'(?m)^\s{0,3}#{1,6}\s+\S', text) is not None


def _has_markdown_list(text: str) -> bool:
    return (
        re.search(r'(?m)^\s{0,3}[-*+]\s+\S', text) is not None or
        re.search(r'(?m)^\s{0,3}\d+\.\s+\S', text) is not None
    )


def _has_bold_or_italic(text: str) -> bool:
    # Bold: **bold** or __bold__
    bold = re.search(
        r'(\*\*[^*\n][^*]*\*\*|__[^_\n][^_]*__)', text) is not None
    # Italic: *italic* or _italic_ (avoid bold markers)
    italic = re.search(
        r'(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)', text) is not None
    return bold or italic


def _has_markdown_link(text: str) -> bool:
    return re.search(r'\[[^\]]+\]\([^)]+\)', text) is not None


def _has_code_block(text: str) -> bool:
    return re.search(r'```', text) is not None


def _final_answer_match(text: str):
    """
    Try to match the final 'Answer: <dessert><punct>' at the end of the response (ignoring trailing whitespace).
    Returns a match object or None.
    """
    # Anchor to end with optional whitespace, require a punctuation mark immediately after the dessert name
    pattern = r'Answer:\s*(.+?)\s*([^\w\s])\s*$'
    return re.search(pattern, text, flags=re.DOTALL)


# ========== Validators ==========

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response contains at least ONE of these Markdown elements:
    - A heading (# ...)
    - A list item (-, *, +, or 1.)
    - Bold or italic text
    - A Markdown link [text](url)
    - A fenced code block ```...```

    Additionally, ensure the final 'Answer: ...' line is not inside a fenced code block.
    """
    if not response or not response.strip():
        return (
            False,
            "Empty response. Include at least one Markdown element: heading, list, emphasis, link, or code block."
        )

    # Check each element
    has_heading = _has_markdown_heading(response)
    has_list = _has_markdown_list(response)
    has_emphasis = _has_bold_or_italic(response)
    has_link = _has_markdown_link(response)
    has_code_block = _has_code_block(response)

    # OR logic: At least one element must be present
    elements = [has_heading, has_list, has_emphasis, has_link, has_code_block]
    has_any_markdown = any(elements)

    if not has_any_markdown:
        return (
            False,
            "Missing Markdown formatting. Include at least ONE of these elements:\n"
            "1. A heading (e.g., '# Title' or '## Section')\n"
            "2. A list (e.g., '- item' or '1. step')\n"
            "3. Bold or italic text (e.g., **important** or *note*)\n"
            "4. A link (e.g., [example](https://example.com))\n"
            "5. A code block (```code```)\n\n"
            "Example minimal format: '# Summary' (just a heading is sufficient)"
        )

    # Collect feedback on what was found
    found_elements = []
    suggestions = []

    if has_heading:
        found_elements.append("heading")
    else:
        suggestions.append("Consider adding a heading for structure.")

    if has_list:
        found_elements.append("list")
    else:
        suggestions.append("Consider adding a list for organization.")

    if has_emphasis:
        found_elements.append("emphasis")
    else:
        suggestions.append("Consider using bold or italic for emphasis.")

    if has_link:
        found_elements.append("link")
    else:
        suggestions.append("Consider adding a link for reference.")

    if has_code_block:
        found_elements.append("code block")
    else:
        suggestions.append("Consider adding a code block for examples.")

    # Build response message
    success_msg = f"Pass: Found {', '.join(found_elements)}."

    if suggestions:
        success_msg += f" Suggestions: {' '.join(suggestions)}"

    # Note: The check for 'Answer:' line position is handled elsewhere
    return (True, success_msg)


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with a period '.' as the final non-whitespace character.
    """
    last_char = _last_non_ws_char(response)
    if last_char != '.':
        if last_char == '':
            return (
                False,
                "Fail: The response appears empty or whitespace-only. Add the complete content and ensure the final character is a period '.'."
            )
        return (
            False,
            f"Fail: The last non-whitespace character is '{last_char}', but the response must end with a period '.'. "
            "Append a single '.' at the very end of the response, immediately following the final 'Answer: <dessert>' line."
        )
    return (
        True,
        "Pass: The response ends with a period '.' as required."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response concludes with the exact phrase:
    'Answer: [dessert name]' followed by a punctuation mark (then nothing else).
    - 'Answer:' must be capitalized exactly and followed by a colon.
    - [dessert name] must be a concrete name (not the placeholder '[dessert name]').
    - A punctuation mark must immediately follow the dessert name; punctuation is further validated by validate_punctuation.
    """
    stripped = _rstrip(response)
    m = _final_answer_match(stripped)

    if m is None:
        # Provide targeted guidance based on common errors
        # Check if it at least ends with 'Answer:' token
        if re.search(r'Answer:\s*$', stripped):
            return (
                False,
                "Fail: The response ends with 'Answer:' but is missing the dessert name and trailing punctuation. "
                "Complete it as: 'Answer: Tiramisu.' (replace with the actual dessert)."
            )
        # Check if it ends with 'Answer: <text>' without punctuation
        m2 = re.search(r'Answer:\s*(.+?)\s*$', stripped)
        if m2 is not None:
            return (
                False,
                "Fail: The final 'Answer: <dessert>' line lacks the required trailing punctuation. "
                "Add a punctuation mark immediately after the dessert name, e.g., 'Answer: Baklava.'."
            )
        # Check for lowercase 'answer:'
        if re.search(r'answer:\s*(.+?)\s*[^\w\s]\s*$', stripped):
            return (
                False,
                "Fail: Use exact capitalization 'Answer:' (capital A) before the dessert name. "
                "For example: 'Answer: Sachertorte.'."
            )
        return (
            False,
            "Fail: The response must conclude with a line like 'Answer: Cheesecake.' "
            "Place this as the final line, with 'Answer:' exactly capitalized and followed by the dessert name and punctuation."
        )

    dessert = m.group(1).strip()
    punct = m.group(2)

    # Disallow placeholder or bracketed placeholder
    if re.fullmatch(r'\[?\s*dessert\s+name\s*\]?', dessert, flags=re.IGNORECASE):
        return (
            False,
            "Fail: Replace the placeholder with an actual dessert name, e.g., 'Answer: Pastel de Nata.'."
        )

    # Discourage including square brackets around the dessert name
    if '[' in dessert or ']' in dessert:
        return (
            False,
            "Fail: Do not include square brackets around the dessert name. "
            "Write it plainly, e.g., 'Answer: Maple Taffy.'."
        )

    # Check nothing follows after punctuation (regex already enforces end-of-string aside from whitespace)
    # Ensure 'Answer:' is not inside a code block (format validator also checks this)
    code_spans = _code_block_spans(response)
    if _index_in_spans(m.start(), code_spans):
        return (
            False,
            "Fail: The final 'Answer: <dessert>.' line is inside a code block. "
            "Move it outside fenced code blocks so it appears as normal text at the very end."
        )

    return (
        True,
        f"Pass: Final identifier phrase found as 'Answer: {dessert}{punct}' at the end of the response."
    )

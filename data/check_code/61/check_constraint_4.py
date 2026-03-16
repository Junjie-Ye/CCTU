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
 The answer must conclude with the phrase "[End of Answer]", be determined within at most 8 interaction turns with the tools. Usage of the `seafood_origin_locator` is conditional upon the prior execution of the `port_locator` tool. Use the seafood_origin_locator tool at most 1 time, and present the final answer using Markdown syntax with at least one bolded element highlighting the local spice.

response_constraints_non_length:
- idx 0: ('Response', 'Identifiers', 'End identifier (The agent\'s response must conclude with the phrase "[End of Answer]" to signal the completion of the answer clearly and consistently.)')
- idx 4: ('Response', 'Format', "The agent's final answer must be formatted using Markdown syntax, including at least one bolded element to highlight the local spice.")
"""

import re
from typing import List, Tuple

# ============================================================
# Helpers
# ============================================================

END_TAG = "[End of Answer]"

# Regex to strip fenced code blocks so bold inside code doesn't falsely satisfy checks.
FENCED_CODE_BLOCK_RE = re.compile(r"```.*?```", flags=re.DOTALL)

# Regex patterns to find Markdown bold segments.
BOLD_PATTERNS = [
    re.compile(r"\*\*(.+?)\*\*"),   # **bold**
    re.compile(r"__(.+?)__"),       # __bold__
]

# Regex to detect the word "spice" (or "spices") in context, case-insensitive.
SPICE_WORD_RE = re.compile(r"\bspice(s)?\b", flags=re.IGNORECASE)

# Characters allowed inside a plausible spice name (letters, spaces, hyphens, and apostrophes).
PLAUSIBLE_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z\s\-'’]{0,60}$")


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks to avoid counting bold markers inside code."""
    return FENCED_CODE_BLOCK_RE.sub("", text)


def _extract_bold_segments(text: str) -> List[Tuple[str, int, int]]:
    """
    Return a list of (segment_text, start_index, end_index) for all markdown bold segments.
    Searches the provided text as-is (caller should strip code blocks if desired).
    """
    segments: List[Tuple[str, int, int]] = []
    for pat in BOLD_PATTERNS:
        for m in pat.finditer(text):
            segments.append((m.group(1).strip(), m.start(), m.end()))
    return segments


def _looks_like_spice_name(bold_text: str) -> bool:
    """
    Heuristic: A spice name is typically a short phrase (1-4 words), composed of letters
    and simple separators. Avoid long sentences or segments containing digits/URLs.
    """
    if not bold_text:
        return False

    # Must look like a token/short phrase
    if not PLAUSIBLE_TOKEN_RE.match(bold_text):
        return False

    # Word count check
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-'’]*", bold_text)]
    if not (1 <= len(words) <= 4):
        return False

    return True


def _has_spice_context_nearby(text: str, start: int, end: int, window: int = 80) -> bool:
    """
    Check whether the word 'spice' (or 'spices') appears within a nearby window
    around the bold segment to indicate it is explicitly highlighted as a spice.
    """
    left = max(0, start - window)
    right = min(len(text), end + window)
    context = text[left:right]
    return SPICE_WORD_RE.search(context) is not None


# ============================================================
# Validators
# ============================================================

def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Constraint:
    - End identifier: The agent's response must conclude with the phrase "[End of Answer]".

    Returns:
    - (True, message) if valid.
    - (False, detailed guidance) if invalid.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a complete answer and ensure it ends exactly with '[End of Answer]'."
        )

    trimmed_end = response.rstrip()
    if trimmed_end.endswith(END_TAG):
        return (
            True,
            "Valid: The response ends exactly with '[End of Answer]'."
        )

    # Check if a similar tag is present but misplaced or mistyped
    lower_resp = response.lower()
    if "[end of answer]" in lower_resp and not trimmed_end.endswith(END_TAG):
        return (
            False,
            "The completion tag must be the very last non-whitespace content and must match exactly '[End of Answer]' (case and brackets included). "
            "Move the exact tag to the end of the response with no characters (including punctuation) after it. Example:\n\n"
            "... final sentence.\n[End of Answer]"
        )

    return (
        False,
        "Missing or incorrect end identifier. Conclude the response with the exact phrase '[End of Answer]' as the final non-whitespace characters. "
        "Do not add any punctuation or text after it. Example:\n\n"
        "... final sentence.\n[End of Answer]"
    )


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Constraint:
    - The final answer must be formatted using Markdown syntax, including at least one bolded element
      to highlight the local spice.

    Checks performed:
    1) There is at least one Markdown bold segment (**bold** or __bold__).
    2) At least one bold segment plausibly represents a local spice name (short, token-like), OR
       the text around a bold segment explicitly references 'spice/spices'.

    Returns:
    - (True, message) if valid.
    - (False, detailed guidance) if invalid.
    """
    if not isinstance(response, str) or not response.strip():
        return (
            False,
            "The response is empty or not a string. Provide a Markdown-formatted answer with at least one bold element highlighting the local spice (e.g., '**Kashmiri chili**')."
        )

    # Remove fenced code blocks to avoid counting bold markers inside code
    scan_text = _strip_code_blocks(response)

    # Detect Markdown bold segments
    bold_segments = _extract_bold_segments(scan_text)

    # If HTML bold was used, guide to replace with Markdown bold
    if "<b>" in response.lower() or "</b>" in response.lower():
        return (
            False,
            "HTML <b> tags detected. Use Markdown bold instead, e.g., '**local spice name**'. Ensure at least one bolded element highlights the local spice."
        )

    if not bold_segments:
        return (
            False,
            "No Markdown bold detected. Add at least one bolded element using '**' or '__' to highlight the local spice (e.g., '**Berbere**', '**Sichuan peppercorn**')."
        )

    # Validate that at least one bold segment plausibly highlights a local spice
    has_valid_spice_highlight = False
    for seg_text, start, end in bold_segments:
        if _looks_like_spice_name(seg_text) or _has_spice_context_nearby(scan_text, start, end):
            has_valid_spice_highlight = True
            break

    if not has_valid_spice_highlight:
        return (
            False,
            "Bold text is present but it does not appear to highlight a local spice. "
            "Ensure at least one bold segment is a concise spice/seasoning name (1–4 words) or is clearly labeled as a spice in nearby text. "
            "Examples: '**Vadouvan**', '**Espelette pepper**', or include 'spice' near it: 'local spice: **Berbere**'."
        )

    return (
        True,
        "Valid: Markdown bold is present and at least one bold segment plausibly highlights a local spice."
    )

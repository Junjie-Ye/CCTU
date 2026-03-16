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
 The final answer must be formatted in Markdown syntax, including the use of headings, bold/italic text, and clear numerical comparisons to enhance readability and clarity. Additionally, the response must conclude with the exact phrase "**Answer:** (a) is more than (b)" or "**Answer:** (b) is more than (a)", depending on the result. The response must not include any periods. If the agent uses the `cultural_heritage_locator` tool, the `mountain_peak_identifier` tool must be called afterwards. In at least one interaction turn, the agent must invoke at least 2 unique tool types in parallel.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The final answer must be formatted in Markdown syntax, including the use of headings, bold/italic text, and clear numerical comparisons to enhance readability and clarity.')
- idx 1: ('Response', 'Identifiers', '(Main Category, Subcategory, Specific Constraint): ("Response", "End identifier", "The response must conclude with the exact phrase \'**Answer:** (a) is more than (b)\' or \'**Answer:** (b) is more than (a)\', depending on the result.")')
- idx 2: ('Response', 'Punctuation', "(Response, Punctuation, Exclude punctuation (Mandates that periods must not be used in the agent's response, helping to maintain a specific tone or style.))")
"""

import re
from typing import Tuple, List

# Helpers


def _rstrip_final(text: str) -> str:
    """Strip trailing whitespace and newlines from the right."""
    return text.rstrip()


def _has_markdown_heading(text: str) -> bool:
    """
    Detect at least one Markdown ATX heading, e.g., "# Heading", "## Heading", up to "###### Heading".
    Allows up to 3 leading spaces as per commonmark.
    """
    return re.search(r'(?m)^\s{0,3}#{1,6}\s+\S', text) is not None


def _has_bold_or_italic(text: str) -> bool:
    """
    Detect bold or italic emphasis segments in Markdown.
    - Bold: **text** or __text__
    - Italic: *text* or _text_
    Avoids matching list bullets by requiring surrounding markers on both sides.
    """
    bold_pat = r'(\*\*[^*\n][^*\n]*\*\*|__[^_\n][^_\n]*__)'
    italic_pat = r'(?<!\*)\*[^*\n][^*\n]*\*(?!\*)|(?<!_)_[^_\n][^_\n]*_(?!_)'
    return re.search(bold_pat, text) is not None or re.search(italic_pat, text) is not None


def _has_clear_numerical_comparison(text: str) -> bool:
    """
    Heuristics for "clear numerical comparisons":
    Pass if any of the following is true:
      1) There is an explicit numeric comparator like 12 > 9, 7 < 8, 10 = 10, including ≥ or ≤
      2) The text includes at least two numbers and a comparison phrase (more than, less than, greater than, fewer than, versus, vs)
      3) There are lines for (a) and (b) each containing at least one number
    """
    # 1) Explicit comparator
    if re.search(r'\b\d+(?:\.\d+)?\s*(?:[><=]|≥|≤)\s*\d+(?:\.\d+)?\b', text):
        return True

    # 2) Two or more numbers plus comparison phrase
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
    comp_phrases = [
        r'\bmore than\b',
        r'\bless than\b',
        r'\bgreater than\b',
        r'\bfewer than\b',
        r'\bversus\b',
        r'\bvs\b',
        r'\bcompare\b',
        r'\bcomparison\b',
        r'\bdifference\b'
    ]
    if len(numbers) >= 2 and any(re.search(p, text, flags=re.IGNORECASE) for p in comp_phrases):
        return True

    # 3) Lines for (a) and (b) each with at least one number
    has_a_num = re.search(r'\(a\).*?\b\d+(?:\.\d+)?\b',
                          text, flags=re.IGNORECASE | re.DOTALL) is not None
    has_b_num = re.search(r'\(b\).*?\b\d+(?:\.\d+)?\b',
                          text, flags=re.IGNORECASE | re.DOTALL) is not None
    if has_a_num and has_b_num:
        return True

    return False


def _find_prohibited_period_positions(text: str) -> List[int]:
    """Return zero-based indices of '.' or '。' characters."""
    return [m.start() for m in re.finditer(r'[\.。]', text)]

# Validators


def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the final answer is formatted in Markdown syntax, including:
    - Headings (at least one line starting with # followed by a space)
    - Bold or italic emphasis (**bold** or *italic*)
    - Clear numerical comparisons
    """
    has_heading = _has_markdown_heading(response)
    has_emphasis = _has_bold_or_italic(response)
    has_num_compare = _has_clear_numerical_comparison(response)

    missing: List[str] = []
    if not has_heading:
        missing.append(
            "- Add at least one Markdown heading line, e.g., '# Title' or '## Summary'")
    if not has_emphasis:
        missing.append(
            "- Include bold or italic emphasis, e.g., '**Key result**' or '*Note*'")
    if not has_num_compare:
        missing.append(
            "- Provide a clear numerical comparison: either show an explicit comparator like '12 > 9', "
            "use a comparison phrase such as 'more than' or 'less than' while presenting at least two numbers, "
            "or present numeric values for both (a) and (b)"
        )

    if missing:
        guidance = (
            "Format validation failed. The final answer must use Markdown with headings, emphasis, and clear numerical comparisons.\n"
            + "\n".join(missing) +
            "\nExample structure (adjust content to your case):\n"
            "# Comparison Summary\n"
            "- (a): 12\n"
            "- (b): 9\n"
            "**Conclusion**: 12 > 9\n"
            "**Answer:** (a) is more than (b)"
        )
        return False, guidance

    return True, "Format validation passed."


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate that no periods are used anywhere in the response.
    Prohibited characters: '.' and '。'
    Note: For decimals, rewrite without periods (e.g., '3.5' -> '3 point 5').
    """
    positions = _find_prohibited_period_positions(response)
    if positions:
        preview_examples = []
        for idx in positions[:5]:
            start = max(0, idx - 15)
            end = min(len(response), idx + 16)
            snippet = response[start:end].replace("\n", "\\n")
            preview_examples.append(f"...{snippet}...")
        details = (
            "Punctuation validation failed: periods are not allowed. "
            "Remove '.' and '。' from the response. Replace sentence-ending periods with line breaks or semicolons, "
            "and rewrite decimals using words (e.g., '3 point 5').\n"
            f"Found {len(positions)} prohibited characters at positions: {positions[:20]} "
            f"(showing up to first 20). Snippets:\n" +
            "\n".join(preview_examples)
        )
        return False, details

    return True, "Punctuation validation passed."


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that the response ends with exactly one of the required phrases:
    - '**Answer:** (a) is more than (b)'
    - '**Answer:** (b) is more than (a)'
    No extra characters or whitespace after the phrase are allowed.
    """
    required_endings = [
        "**Answer:** (a) is more than (b)",
        "**Answer:** (b) is more than (a)",
    ]
    trimmed = _rstrip_final(response)

    if any(trimmed.endswith(e) for e in required_endings):
        # Ensure there is nothing after the ending in the original response except whitespace
        ending = next(e for e in required_endings if trimmed.endswith(e))
        # whitespace-only tail allowed
        tail = response[len(response.rstrip()):]
        if tail == "" or tail.isspace():
            return True, "Identifier validation passed."
        # Technically rstrip removed all trailing whitespace; if any remained in original, it's whitespace.
        return True, "Identifier validation passed."

    guidance = (
        "Identifier validation failed: the response must end with exactly one of the following phrases, "
        "with no extra characters or whitespace after it:\n"
        "- **Answer:** (a) is more than (b)\n"
        "- **Answer:** (b) is more than (a)\n"
        "Ensure the phrase is the final non-whitespace content."
    )
    return False, guidance

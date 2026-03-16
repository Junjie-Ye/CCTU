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
 The answer must not include any unnecessary punctuation marks such as commas or periods within the list of countries, as it may interfere with clarity and precision. Additionally, the response must end with a period to ensure complete and grammatically correct sentence closure.

response_constraints_non_length:
- idx 0: ('Response', 'Punctuation', 'The answer must not include any unnecessary punctuation marks such as commas or periods within the list of countries, as it may interfere with clarity and precision.')
"""

import re
from typing import Tuple, List, Dict

# Helper: extract the content that will actually be judged as the "answer".
# If a [FINAL ANSWER] section exists, validate only that section. Otherwise, validate the whole response.


def _extract_final_answer_segment(response: str) -> str:
    m = re.search(r'\[FINAL ANSWER\](.*)$', response,
                  flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return response.strip()

# Helper: detect inline uses of commas or periods between country-like names.
# We use a heuristic: sequences of 1-4 capitalized tokens (to allow "United States", "Costa Rica", etc.).
# This is not a strict NER solution but is robust enough for enforcing the punctuation rule.


def _find_inline_country_punct_issues(text: str) -> Dict[str, List[str]]:
    issues = {
        "comma_pairs": [],   # e.g., "France, Germany"
        "period_pairs": []   # e.g., "France. Germany"
    }

    # Capitalized multi-word chunk (1 to 4 tokens) such as "France", "United States", "Costa Rica"
    cap_chunk = r'(?:[A-Z][A-Za-z’\'\-]+(?:\s+[A-Z][A-Za-z’\'\-]+){0,3})'

    # Comma used between two capitalized chunks
    comma_pattern = re.compile(rf'\b({cap_chunk})\s*,\s*({cap_chunk})\b')
    # Period used between two capitalized chunks (not end-of-text, i.e., followed by space and another chunk)
    period_pattern = re.compile(rf'\b({cap_chunk})\.\s+({cap_chunk})\b')

    for m in comma_pattern.finditer(text):
        left, right = m.group(1), m.group(2)
        issues["comma_pairs"].append(f"{left}, {right}")

    for m in period_pattern.finditer(text):
        left, right = m.group(1), m.group(2)
        issues["period_pairs"].append(f"{left}. {right}")

    return issues

# Helper: detect bullet/numbered list items that include commas or periods within the item text.
# If a bullet item looks like a country entry, any comma/period inside the item is considered a violation.


def _find_bullet_item_punct_issues(text: str) -> List[str]:
    offending_items = []
    # Match typical bullet lines: "-", "*", "•", "1.", "2)", "1)" etc.
    bullet_re = re.compile(
        r'^\s*(?:[-*•]|(?:\d+[\.\)]))\s*(.+?)\s*$', re.MULTILINE)

    # Heuristic for "country-like" item: starts with a capitalized token and has no lowercase sentence structure
    # (we keep it simple to avoid false negatives).
    country_like_start = re.compile(
        r'^[A-Z][A-Za-z’\'\-]+(?:\s+[A-Z][A-Za-z’\'\-]+){0,3}$')

    for m in bullet_re.finditer(text):
        item = m.group(1).strip()
        # If there are commas or periods in the item, and the item is likely a country name, flag it.
        if ("," in item or "." in item):
            # Remove trailing annotations like "(...)" before judging "country-likeness"
            base = re.sub(r'\s*\(.*?\)\s*$', '', item).strip()
            # If the base still contains commas/periods, it's a violation for country-like entries.
            if re.search(r'[.,]', base):
                offending_items.append(item)
            else:
                # If base is clean but original had punctuation elsewhere, still consider it suspect when country-like.
                if country_like_start.match(base):
                    offending_items.append(item)
    return offending_items

# Helper: check ending punctuation requirements.


def _check_final_period(text: str) -> Tuple[bool, str]:
    stripped = text.rstrip()
    if not stripped.endswith('.'):
        return False, "The response must end with a single period. Add one period at the very end of the answer."
    # Disallow multiple trailing periods like "...."
    # Accept exactly one final '.' followed only by whitespace.
    if re.search(r'\.\s*$', stripped) and re.search(r'\.\.+\s*$', stripped):
        return False, "End the response with exactly one period. Remove any extra trailing periods."
    return True, ""


def validate_punctuation(response: str) -> Tuple[bool, str]:
    """
    Validate punctuation rules for the response:
    - Do not use commas or periods inside the list of countries.
    - The response must end with a single period.
    Returns (is_valid, detailed_english_message).
    """
    segment = _extract_final_answer_segment(response)

    # 1) Check final period rule
    ok_end, end_msg = _check_final_period(segment)

    # 2) Check for commas/periods used within country lists (heuristic)
    inline_issues = _find_inline_country_punct_issues(segment)
    bullet_issues = _find_bullet_item_punct_issues(segment)

    problems: List[str] = []
    if not ok_end:
        problems.append(f"- Ending period: {end_msg}")

    if inline_issues["comma_pairs"]:
        examples = "; ".join(inline_issues["comma_pairs"][:3])
        more = "" if len(
            inline_issues["comma_pairs"]) <= 3 else f" (and {len(inline_issues['comma_pairs']) - 3} more)"
        problems.append(
            f"- Do not use commas between country names. Found examples: {examples}{more}. Replace commas with newlines or spaces.")
    if inline_issues["period_pairs"]:
        examples = "; ".join(inline_issues["period_pairs"][:3])
        more = "" if len(
            inline_issues["period_pairs"]) <= 3 else f" (and {len(inline_issues['period_pairs']) - 3} more)"
        problems.append(
            f"- Do not use periods as separators between country names. Found examples: {examples}{more}. Use newlines or spaces instead.")

    if bullet_issues:
        examples = "; ".join(bullet_issues[:3])
        more = "" if len(
            bullet_issues) <= 3 else f" (and {len(bullet_issues) - 3} more)"
        problems.append(
            f"- Bullet list items must not include commas or periods inside the country entry. Offending items: {examples}{more}.")

    if problems:
        guidance = (
            "Please format the list of countries without commas or periods inside the list. "
            "Acceptable separators are newlines or simple spaces. For example:\n"
            "- France\n- Germany\n- Spain\n"
            "Ensure the entire response ends with exactly one period."
        )
        return False, "Punctuation violations detected:\n" + "\n".join(problems) + "\n" + guidance

    return True, "Punctuation is valid: no commas or periods appear within the list of countries and the response ends with a single period."

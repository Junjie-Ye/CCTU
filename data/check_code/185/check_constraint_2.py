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

import re
from typing import Tuple, List, Pattern

# ----------------------------
# Helper utilities
# ----------------------------
HEIGHT_PATTERN: Pattern = re.compile(
    r'(?P<value>\d{1,3}(?:,\d{3})*|\d+)(?:\.(?:\d+))?\s*(?P<unit>m|meter|meters|metre|metres)\b',
    flags=re.IGNORECASE
)
TALLER_KEYWORD_RE: Pattern = re.compile(
    r"(?ix)\b("
    r"taller|higher|height|elevation|altitude|vertical\s+drop|vertical\s+rise|"
    r"exceed(?:s|ed|ing)?|surpass(?:es|ed|ing)?|out(?:-| )?rank(?:s|ed|ing)?|"
    r"out(?:-| )?strip(?:s|ped|ping)?|overtake(?:s|n)?|"
    r"greater(?:\s+than)?|more(?:\s+than)?|less(?:\s+than)?|"
    r"larger(?:\s+than)?|smaller(?:\s+than)?|"
    r"bigger(?:\s+than)?|lower(?:\s+than)?|"
    r"maximum|min(?:imum)?|"
    r">=|<=|>|<|=|"
    r"the\s+(?:taller|higher|larger|greater)\s+(?:one|option|choice|structure|site)|"
    r"(?:option|choice)\s*(?:a|b)\s*is\s*(?:taller|higher|larger|greater)|"
    r"(?:a|b)\s*is\s*(?:taller|higher|larger|greater)"
    r")\b"
)
TALLER_KEYWORD_RE: Pattern = re.compile(r'\b(taller|higher)\b', re.IGNORECASE)


def _strip_trailing_whitespace(text: str) -> str:
    return text.rstrip()


def _has_taller_keyword(text: str) -> bool:
    return bool(TALLER_KEYWORD_RE.search(text or ""))


def _find_heights_in_meters(text: str) -> List[str]:
    return [m.group(0) for m in HEIGHT_PATTERN.finditer(text or "")]

# ----------------------------
# Validators
# ----------------------------


def validate_punctuation(response: str) -> Tuple[bool, str]:
    trimmed = _strip_trailing_whitespace(response)
    if not trimmed:
        return (False, "The response is empty. Provide a final answer and ensure it ends with a period '.'.")
    if not trimmed.endswith("."):
        return (False, "The response must end with a period '.'. Trim trailing whitespace/newlines and append a final period.")
    return (True, "Pass: The response ends with a period.")


def validate_identifiers(response: str) -> Tuple[bool, str]:
    if not response or not response.strip():
        return (
            False,
            "The response is empty. Include 'taller' (or 'higher') and provide both heights in meters, ending with a period."
        )

    text = _strip_trailing_whitespace(response)

    if not _has_taller_keyword(text):
        return (
            False,
            "Include a height comparison keyword such as 'taller' or 'higher' somewhere in the response."
        )

    heights = _find_heights_in_meters(text)
    if len(heights) < 2:
        return (
            False,
            "The response must include the specific heights of both options in meters (e.g., '324 m' and '96 m'). "
            "Add two heights with meter units anywhere in the response."
        )

    return (
        True,
        "Pass: The response contains a taller/higher keyword and includes at least two heights in meters."
    )

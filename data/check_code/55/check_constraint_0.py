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
 Your answer must contain a **tabular format**, clearly summarizing the chain of information retrieval steps and the final result. Additionally, the response must include the delimiter "###" to separate the information retrieval steps from the final result in the tabular format. The solution must use between 5 and 7 tool calls to complete the task. The `local_culture_explorer` tool can only be invoked if the `historical_figure_locator` has already been executed within the trajectory.

response_constraints_non_length:
- idx 0: ('Response', 'Format', 'The answer must contain a **tabular format**, clearly summarizing the chain of information retrieval steps and the final result.')
- idx 1: ('Response', 'Identifiers', '(Response, Delimiting identifier, The response must include the delimiter "###" to separate the information retrieval steps from the final result in the tabular format.)')
"""

import re
from typing import Tuple, List, Optional

# ---------------------------
# Helpers
# ---------------------------

DELIM = "###"
DELIM_LINE_RE = re.compile(r"^\s*###\s*$")


def _split_by_delimiter_loose(response: str, delimiter: str = DELIM) -> Tuple[List[str], List[str], int]:
    if not response:
        return [], [], 0

    lines = response.splitlines()

    # 1) 优先：把 “单独一行 ###” 当 delimiter
    delim_indices = [i for i, line in enumerate(
        lines) if DELIM_LINE_RE.match(line)]
    if delim_indices:
        first = delim_indices[0]
        pre = lines[:first]
        post = lines[first + 1:]
        return pre, post, len(delim_indices)

    # 2) 退化：不要求单独一行，只要文本里出现过 "###" 就切
    if delimiter in response:
        idx = response.find(delimiter)
        pre_text = response[:idx]
        post_text = response[idx + len(delimiter):]
        # 这里 count 用粗略 count（不严格）
        return pre_text.splitlines(), post_text.splitlines(), response.count(delimiter)

    return lines, [], 0


def _is_table_line(line: str) -> bool:
    if not line or not line.strip():
        return False
    return line.count("|") >= 2


def _extract_tables_loose(lines: List[str]) -> List[List[str]]:
    tables = []
    current = []
    for line in lines:
        if _is_table_line(line):
            current.append(line)
        else:
            if len(current) >= 1:
                tables.append(current)
            current = []
    if len(current) >= 1:
        tables.append(current)
    return tables


# ---------------------------
# Validators
# ---------------------------

def validate_identifiers(response: str) -> Tuple[bool, str]:
    if response is None or not isinstance(response, str) or not response.strip():
        return (False, "The response is empty. Include the delimiter '###' to separate steps from final result.")

    if "###" not in response:
        return (
            False,
            "The response must include the delimiter '###' to separate the information retrieval steps from the final result."
        )

    return (True, "Delimiter '###' is present.")


def validate_format(response: str) -> Tuple[bool, str]:
    if response is None or not isinstance(response, str) or not response.strip():
        return (False, "The response is empty. Provide tabular content and a '###' delimiter.")

    pre, post, delimiter_count = _split_by_delimiter_loose(response, "###")

    if delimiter_count == 0:
        return (
            False,
            "Missing delimiter '###'. Add '###' between a steps table and a final result table."
        )

    pre_tables = _extract_tables_loose(pre)
    post_tables = _extract_tables_loose(post)

    if len(pre_tables) == 0:
        return (
            False,
            "There is no tabular (table-like) content before the '###' delimiter. "
            "Add a Markdown-style table summarizing the information retrieval steps above '###'."
        )

    if len(post_tables) == 0:
        return (
            False,
            "There is no tabular (table-like) content after the '###' delimiter. "
            "Add a Markdown-style table for the final result below '###'."
        )

    return (
        True,
        "Valid: delimiter exists, and there is table-like content both before and after the delimiter."
    )

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
 You must solve this by calling the available tools and not by directly answering the question. If a tool call fails, you must analyze the error, correct the parameters, and retry until you arrive at an answer. You are allowed to make at most 5 interaction rounds to solve this. Additionally, the geopolitical_event_finder tool can be invoked at most 2 times during the task. The final answer must be presented in a tabular format, including at least the date, location, involved parties, and a description of the event. The final answer must output the country name in bold. Furthermore, the final answer must be between 50 and 150 characters long, inclusive, to ensure conciseness and clarity.

response_constraints_non_length:
- idx 1: ('Response', 'Identifiers', 'The final response must output the country name in bold.')
- idx 3: ('Response', 'Format', '(Main Category, Subcategory, Specific Constraint): (Format, Table, The final answer must be presented in a tabular format, including at least the date, location, involved parties, and a description of the event.)')
"""

import re
import unicodedata
from typing import List, Tuple, Optional, Dict, Set

# ---------------------------
# Helpers for Markdown tables
# ---------------------------


def _normalize_text(s: str) -> str:
    """
    Lowercase, normalize unicode (remove diacritics), and trim surrounding punctuation.
    Keep letters, digits, spaces, dashes, and apostrophes.
    """
    if s is None:
        return ""
    # Replace curly apostrophes with straight ones
    s = s.replace("’", "'").replace(
        "‘", "'").replace("ʼ", "'").replace("`", "'")
    # Unicode normalize (remove accents)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # Lowercase
    s = s.lower()
    # Trim outer punctuation and whitespace
    s = s.strip(" \t\r\n.,;:!?()[]{}\"“”‘’|")
    # Collapse internal whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def _split_md_row(line: str) -> List[str]:
    """
    Split a Markdown table row into cells, trimming outer pipes and spaces.
    Example: "| a | b |" -> ["a", "b"]
    """
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # Split by '|' and strip spaces
    cells = [c.strip() for c in line.split("|")]
    return cells


def _is_separator_line(line: str) -> bool:
    """
    Check if a Markdown line is a table separator line (e.g., |---|:---:|---|)
    Each cell must be made of at least 3 dashes, optional surrounding colons and spaces.
    """
    cells = _split_md_row(line)
    if not cells:
        return False
    for c in cells:
        if not re.fullmatch(r"\s*:?-{3,}:?\s*", c):
            return False
    return True


def _extract_first_md_table(text: str) -> Optional[Dict[str, List[List[str]]]]:
    """
    Extract the first Markdown table found in the text.
    Supports:
      A) Normal Markdown table: header + separator + >=1 data row
      B) Headerless single-row "table": one row with >=4 cells, no separator line required
    """
    lines = text.splitlines()
    i = 0
    n = len(lines)

    # -------- A) Original logic: header + separator + data rows --------
    while i < n:
        if "|" in lines[i].strip():
            header_line = lines[i]
            header_cells = _split_md_row(header_line)
            if len([c for c in header_cells if c != ""]) >= 2:
                if i + 1 < n and _is_separator_line(lines[i + 1]):
                    j = i + 2
                    data_rows: List[List[str]] = []
                    while j < n and "|" in lines[j].strip():
                        row_cells = _split_md_row(lines[j])
                        if any(cell.strip() for cell in row_cells):
                            data_rows.append(row_cells)
                        j += 1
                    return {"headers": header_cells, "rows": data_rows}
        i += 1

    # -------- B) Fallback: headerless single-row table --------
    DEFAULT_HEADERS = ["Date", "Location", "Involved Parties", "Description"]

    for line in lines:
        if "|" not in line.strip():
            continue
        if _is_separator_line(line):
            continue
        cells = _split_md_row(line)
        non_empty = [c for c in cells if c.strip()]
        # Require at least 4 meaningful cells: date/location/involved/description
        if len(non_empty) >= 4:
            # Use first 4 cells, pad if needed (defensive)
            row = cells[:4]
            if len(row) < 4:
                row += [""] * (4 - len(row))
            return {"headers": DEFAULT_HEADERS, "rows": [row]}

    return None


def _find_header_indices(headers: List[str], required_synonyms: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Find indices for required logical columns based on header synonyms.
    Returns mapping from logical key -> header index. Missing keys are excluded.
    Matching is case-insensitive and diacritic-insensitive.
    """
    norm_headers = [_normalize_text(h) for h in headers]
    mapping: Dict[str, int] = {}
    for logical_key, synonyms in required_synonyms.items():
        norm_syns = [_normalize_text(s) for s in synonyms]
        idx = None
        for si, h in enumerate(norm_headers):
            # A header matches if it equals any synonym or contains it as a word
            if h in norm_syns:
                idx = si
                break
            # Also allow partial match if synonym is contained as a token
            for syn in norm_syns:
                if syn and (syn == h or syn in h):
                    idx = si
                    break
            if idx is not None:
                break
        if idx is not None:
            mapping[logical_key] = idx
    return mapping


# -----------------------------------
# Country name detection (bold check)
# -----------------------------------

def _country_set() -> Set[str]:
    """
    Returns a normalized set of widely recognized country names and common variants.
    Normalization matches _normalize_text().
    """
    countries = {
        # UN members and common variants
        "afghanistan", "albania", "algeria", "andorra", "angola", "antigua and barbuda",
        "argentina", "armenia", "australia", "austria", "azerbaijan", "bahamas", "bahrain",
        "bangladesh", "barbados", "belarus", "belgium", "belize", "benin", "bhutan",
        "bolivia", "plurinational state of bolivia", "bosnia and herzegovina", "botswana",
        "brazil", "brunei", "brunei darussalam", "bulgaria", "burkina faso", "burundi",
        "cabo verde", "cape verde", "cambodia", "cameroon", "canada", "central african republic",
        "chad", "chile", "china", "colombia", "comoros", "congo", "republic of the congo",
        "congo-brazzaville", "costa rica", "cote d'ivoire", "cote d ivoire", "ivory coast",
        "croatia", "cuba", "cyprus", "czech republic", "czechia", "democratic republic of the congo",
        "dr congo", "congo-kinshasa", "denmark", "djibouti", "dominica", "dominican republic",
        "ecuador", "egypt", "el salvador", "equatorial guinea", "eritrea", "estonia", "eswatini",
        "swaziland", "ethiopia", "fiji", "finland", "france", "gabon", "gambia", "georgia",
        "germany", "ghana", "greece", "grenada", "guatemala", "guinea", "guinea-bissau",
        "guyana", "haiti", "honduras", "hungary", "iceland", "india", "indonesia",
        "iran", "islamic republic of iran", "iraq", "ireland", "israel", "italy", "jamaica",
        "japan", "jordan", "kazakhstan", "kenya", "kiribati", "korea, democratic people's republic of",
        "north korea", "democratic people's republic of korea", "korea, republic of", "south korea",
        "republic of korea", "kuwait", "kyrgyzstan", "laos", "lao pdr", "lao people's democratic republic",
        "latvia", "lebanon", "lesotho", "liberia", "libya", "liechtenstein", "lithuania",
        "luxembourg", "madagascar", "malawi", "malaysia", "maldives", "mali", "malta",
        "marshall islands", "mauritania", "mauritius", "mexico", "micronesia", "federated states of micronesia",
        "moldova", "republic of moldova", "monaco", "mongolia", "montenegro", "morocco", "mozambique",
        "myanmar", "burma", "namibia", "nauru", "nepal", "netherlands", "new zealand",
        "nicaragua", "niger", "nigeria", "north macedonia", "norway", "oman", "pakistan",
        "palau", "panama", "papua new guinea", "paraguay", "peru", "philippines", "poland",
        "portugal", "qatar", "romania", "russia", "russian federation", "rwanda",
        "saint kitts and nevis", "st kitts and nevis", "saint lucia", "st lucia",
        "saint vincent and the grenadines", "st vincent and the grenadines", "samoa",
        "san marino", "sao tome and principe", "saudi arabia", "senegal", "serbia",
        "seychelles", "sierra leone", "singapore", "slovakia", "slovenia", "solomon islands",
        "somalia", "south africa", "south sudan", "spain", "sri lanka", "sudan", "suriname",
        "sweden", "switzerland", "syria", "syrian arab republic", "taiwan", "chinese taipei",
        "tajikistan", "tanzania", "united republic of tanzania", "thailand", "timor-leste",
        "east timor", "togo", "tonga", "trinidad and tobago", "tunisia", "turkey", "türkiye",
        "turkmenistan", "tuvalu", "uganda", "ukraine", "united arab emirates", "uae",
        "united kingdom", "uk", "great britain", "britain", "united states", "united states of america",
        "usa", "u.s.a", "u.s.", "uruguay", "uzbekistan", "vanuatu", "vatican city", "holy see",
        "venezuela", "venezuela, bolivarian republic of", "vietnam", "viet nam", "yemen",
        "zambia", "zimbabwe", "palestine", "state of palestine", "western sahara"
    }
    # Normalize entries
    return {_normalize_text(c) for c in countries}


_COUNTRIES = _country_set()


def _extract_bold_phrases(text: str) -> List[str]:
    """
    Extract phrases marked as bold using Markdown (** or __) or HTML (<b>, <strong>).
    Returns the raw inner texts (not normalized).
    """
    bolds: List[str] = []
    # Markdown **bold**
    for m in re.finditer(r"\*\*(.+?)\*\*", text, flags=re.DOTALL):
        bolds.append(m.group(1).strip())
    # Markdown __bold__
    for m in re.finditer(r"__(.+?)__", text, flags=re.DOTALL):
        bolds.append(m.group(1).strip())
    # HTML <b>bold</b> or <strong>bold</strong>
    for m in re.finditer(r"<\s*(?:b|strong)\s*>(.*?)<\s*/\s*(?:b|strong)\s*>", text, flags=re.IGNORECASE | re.DOTALL):
        bolds.append(m.group(1).strip())
    return bolds


# ---------------------------------------
# Validators for the specified constraints
# ---------------------------------------

def validate_format(response: str) -> Tuple[bool, str]:
    """
    Validate that the response is presented as a Markdown table containing at least
    the following columns (any order, case-insensitive, with common synonyms accepted):
    - date
    - location
    - involved parties
    - description (of the event)
    Additionally, ensure there is at least one data row and the required cells are non-empty.
    """
    table = _extract_first_md_table(response)
    if not table:
        return (
            False,
            "No Markdown table found. Provide a Markdown table like: "
            "| Date | Location | Involved Parties | Description |\\n"
            "| --- | --- | --- | --- |\\n"
            "| 2025-01-10 | **Ukraine** (Kyiv) | A vs B | Brief event summary |"
        )

    headers = table["headers"]
    rows = table["rows"]

    if len(headers) < 2:
        return (
            False,
            "The table header must contain multiple columns. Include at least: "
            "Date, Location, Involved Parties, Description."
        )

    if not rows:
        return (
            False,
            "The table has no data rows. Add at least one row with all required fields populated."
        )

    # Required columns with synonyms
    required_synonyms = {
        "date": ["date", "event date"],
        "location": ["location", "place", "city", "country"],
        "involved": ["involved parties", "parties", "actors", "involved", "stakeholders"],
        "description": ["description", "event description", "summary", "details", "event"],
    }

    col_map = _find_header_indices(headers, required_synonyms)
    missing = [k for k in required_synonyms.keys() if k not in col_map]
    if missing:
        # Provide user-friendly names in the message
        friendly = {
            "date": "Date",
            "location": "Location",
            "involved": "Involved Parties",
            "description": "Description"
        }
        missing_names = [friendly[m] for m in missing]
        return (
            False,
            f"Missing required columns: {', '.join(missing_names)}. "
            f"Current headers: {', '.join(headers)}. "
            "Add the missing columns exactly (any order) and keep Markdown table syntax with a separator row."
        )

    # Validate the first data row has non-empty required cells
    first_row = rows[0]
    # Pad shorter rows if needed
    if len(first_row) < len(headers):
        first_row = first_row + [""] * (len(headers) - len(first_row))

    empty_fields = []
    for key, idx in col_map.items():
        cell = first_row[idx].strip() if idx < len(first_row) else ""
        if not cell or _normalize_text(cell) in {"", "n/a", "na", "null"}:
            empty_fields.append(key)

    if empty_fields:
        friendly = {
            "date": "Date",
            "location": "Location",
            "involved": "Involved Parties",
            "description": "Description"
        }
        empty_names = [friendly[e] for e in empty_fields]
        return (
            False,
            "The first data row has empty required fields: "
            + ", ".join(empty_names)
            + ". Fill all required cells. Example row: "
              "| 2025-04-02 | **France** (Paris) | Govt & Protesters | Pension reform protests escalate |"
        )

    return (
        True,
        "Format OK. The response contains a valid Markdown table with required columns and data."
    )


def validate_identifiers(response: str) -> Tuple[bool, str]:
    """
    Validate that at least one country name is output in bold.
    Accepted bold syntaxes: **Country**, __Country__, <b>Country</b>, or <strong>Country</strong>.
    The bolded text must correspond to a recognizable country name (common variants allowed).
    """
    bold_phrases = _extract_bold_phrases(response)
    if not bold_phrases:
        return (
            False,
            "No bold text found. Bold the country name using **Country**, __Country__, "
            "<b>Country</b>, or <strong>Country</strong>. Example: **Ukraine**."
        )

    # Check if any bold phrase matches a known country name after normalization
    for raw in bold_phrases:
        norm = _normalize_text(raw)
        if norm in _COUNTRIES:
            return (
                True,
                f"Identifiers OK. Found bold country name: '{raw}'."
            )

    # If no match, provide corrective guidance
    sample = "**United States** or **Ukraine** or <strong>Brazil</strong>"
    return (
        False,
        "Bold text detected but none match a recognized country name. "
        "Ensure the bolded content is a standard country name (no extra words). "
        f"Examples: {sample}. Current bold texts: {', '.join(bold_phrases)}"
    )

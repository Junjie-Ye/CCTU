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


from __future__ import annotations
from typing import Any, Dict, List, Union, Optional
import math


INF = math.inf


def _value_matches_json_type(value: Any, expected: Union[str, List[str], None]) -> bool:
    if expected is None:
        return True

    expected_types = [expected] if isinstance(
        expected, str) else list(expected)

    def _matches_one(v: Any, t: str) -> bool:
        if t == "string":
            return isinstance(v, str)
        if t == "integer":
            return isinstance(v, int) and not isinstance(v, bool)
        if t == "number":
            return isinstance(v, (int, float)) and not isinstance(v, bool)
        if t == "boolean":
            return isinstance(v, bool)
        if t == "object":
            return isinstance(v, dict)
        if t == "array":
            return isinstance(v, list)
        if t == "null":
            return v is None
        return True

    return any(_matches_one(value, t) for t in expected_types)


def validate_param_value(
    param_name: str,
    value: Any,
    schema: Dict[str, Any],
    path: Optional[str] = None,
) -> List[str]:
    errors: List[str] = []
    param_path = path or param_name

    expected_type = schema.get("type")
    if expected_type is not None and (not _value_matches_json_type(value, expected_type)):
        errors.append(
            f"{param_path}: type mismatch, expected {expected_type}, got {type(value).__name__}"
        )
        return errors

    if isinstance(expected_type, str):
        expected_types = [expected_type]
    elif isinstance(expected_type, list):
        expected_types = [t for t in expected_type if isinstance(t, str)]
    elif expected_type is None:
        expected_types = []
    else:
        raise ValueError(f"schema.type invalid: {expected_type!r}")

    # enum
    if "enum" in schema:
        enum_vals = schema["enum"]
        if value not in enum_vals:
            errors.append(
                f"{param_path}: value {value!r} not in enum {enum_vals!r}")

    # object
    if ("object" in expected_types or (expected_type is None and isinstance(value, dict))) and isinstance(value, dict):
        props: Dict[str, Any] = schema.get("properties") or {}
        required: List[str] = schema.get("required") or []

        value_keys = set(value.keys())
        schema_keys = set(props.keys())

        missing = [k for k in required if k not in value_keys]
        if missing:
            errors.append(
                f"{param_path}: missing required fields: {', '.join(missing)}")

        extra = sorted(value_keys - schema_keys)
        if extra:
            errors.append(
                f"{param_path}: extra fields not in schema: {', '.join(extra)}")

        for sub_name, sub_schema in props.items():
            if sub_name not in value:
                continue
            sub_val = value[sub_name]
            sub_path = f"{param_path}.{sub_name}"
            if isinstance(sub_schema, dict):
                errors.extend(validate_param_value(
                    sub_name, sub_val, sub_schema, path=sub_path))

    # array
    if ("array" in expected_types or (expected_type is None and isinstance(value, list))) and isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item_val in enumerate(value):
                item_path = f"{param_path}[{idx}]"
                errors.extend(
                    validate_param_value(
                        f"{param_name}[{idx}]", item_val, item_schema, path=item_path)
                )

    return errors

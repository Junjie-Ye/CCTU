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
import os
import sys
import hashlib
import importlib.util
from functools import lru_cache
from typing import Callable, Any


class ValidatorLoadError(RuntimeError):
    pass


def _stable_module_name(path: str) -> str:
    h = hashlib.md5(os.path.abspath(path).encode("utf-8")).hexdigest()[:12]
    base = os.path.basename(path).replace(".", "_")
    return f"validator_{base}_{h}"


@lru_cache(maxsize=256)
def load_validator_func(validator_path: str, function_name: str) -> Callable[..., Any]:
    if not os.path.exists(validator_path):
        raise FileNotFoundError(f"The validator file does not exist: {validator_path}")

    module_name = _stable_module_name(validator_path)
    try:
        spec = importlib.util.spec_from_file_location(module_name, validator_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec from {validator_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, function_name):
            avail = [n for n in dir(module) if not n.startswith("_")]
            raise AttributeError(f"The module is missing '{function_name}', available functions: {avail}")

        return getattr(module, function_name)
    except Exception as e:
        raise ValidatorLoadError(f"Failed to load validator: {validator_path}::{function_name}: {e}") from e


def call_validator(validator_path: str, function_name: str, *args, **kwargs):
    fn = load_validator_func(validator_path, function_name)
    return fn(*args, **kwargs)

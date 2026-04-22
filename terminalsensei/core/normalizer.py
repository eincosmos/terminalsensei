"""Pattern normalization from parsed commands."""

from __future__ import annotations

import os
import re
from typing import Iterable, List

URL_RE = re.compile(r"^https?://", re.IGNORECASE)
NUM_RE = re.compile(r"^\d+$")
FILE_EXT_RE = re.compile(r".+\.[a-zA-Z0-9]{1,8}$")
PATTERN_RE = re.compile(r"[\*\?\[\]\^\$\|()]")


def classify_arg(arg: str) -> str:
    value = arg.strip()
    if not value:
        return "<arg>"
    if URL_RE.match(value):
        return "<url>"
    if NUM_RE.match(value):
        return "<num>"
    if PATTERN_RE.search(value):
        return "<pattern>"
    if value.endswith("/") or os.path.isdir(os.path.expanduser(value)):
        return "<dir>"
    if FILE_EXT_RE.match(value) or os.path.isfile(os.path.expanduser(value)):
        return "<file>"
    if "/" in value:
        return "<path>"
    return "<arg>"


def normalize_pattern(command_name: str, flags: Iterable[str], args: Iterable[str]) -> str:
    parts: List[str] = [command_name]
    parts.extend(flags)
    parts.extend(classify_arg(arg) for arg in args)
    return " ".join(parts).strip()

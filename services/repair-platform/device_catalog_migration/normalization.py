"""Normalization and ID validation helpers for device catalog migration."""

from __future__ import annotations

import re
from typing import Any


ID_PATTERNS = {
    "DeviceType": re.compile(r"^DT\d+$"),
    "Manufacturer": re.compile(r"^MFG\d+$"),
    "DeviceFamily": re.compile(r"^DF\d+$"),
    "DeviceModel": re.compile(r"^MOD\d+$"),
}


def normalize_header(value: Any) -> str:
    """Return a case/space/punctuation-insensitive header key."""
    if value is None:
        return ""
    return "".join(character.lower() for character in str(value).strip() if character.isalnum())


def normalize_text(value: Any) -> str:
    """Return a normalized text value for matching and comparison."""
    if value is None:
        return ""
    value = str(value).strip()
    value = " ".join(value.split())
    return value.casefold()


def trim_text(value: Any) -> Any:
    """Trim surrounding and repeated whitespace for text values only."""
    if isinstance(value, str):
        return " ".join(value.strip().split())
    return value


def valid_id(entity_type: str, value: Any) -> bool:
    """Return whether value is a valid ID for the entity type."""
    if value is None:
        return False
    pattern = ID_PATTERNS.get(entity_type)
    return bool(pattern and pattern.match(str(value).strip()))


def boolish(value: Any) -> bool | None:
    """Normalize common workbook boolean representations."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = normalize_text(value)
    if text in {"true", "yes", "1", "active"}:
        return True
    if text in {"false", "no", "0", "inactive"}:
        return False
    return None


def format_bool_like(source_value: Any, target_current: Any) -> Any:
    """Format a boolean source value using the target column's existing style."""
    source_bool = boolish(source_value)
    if source_bool is None:
        return source_value
    target_bool = boolish(target_current)
    if isinstance(target_current, bool):
        return source_bool
    text = str(target_current).strip() if target_current is not None else ""
    lower = text.casefold()
    if lower in {"true", "false"}:
        return "TRUE" if source_bool else "FALSE"
    if lower in {"1", "0"}:
        return 1 if source_bool else 0
    return "Yes" if source_bool else "No"

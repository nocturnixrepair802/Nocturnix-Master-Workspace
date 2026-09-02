from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IFixitDeviceResult:
    """Normalized iFixit device or category search result."""

    title: str
    result_type: str
    category: str | None
    url: str | None

    @classmethod
    def from_api_item(cls, item: dict[str, Any]) -> IFixitDeviceResult:
        return cls(
            title=_to_string(
                item.get("display_title") or item.get("title") or item.get("category")
            )
            or "",
            result_type=_to_string(item.get("dataType")) or "category",
            category=_to_string(item.get("category")),
            url=_to_http_url(item.get("url")),
        )

    def to_api_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IFixitGuideMetadata:
    """Normalized guide summary; full guide content is intentionally excluded."""

    guide_id: int | None
    title: str
    category: str | None
    subject: str | None
    guide_type: str | None
    url: str | None
    locale: str | None
    author: str | None
    revision_id: int | None
    modified_date: float | None
    time_required_min: int | None
    time_required_max: int | None
    difficulty: str | None

    @classmethod
    def from_api_item(cls, item: dict[str, Any]) -> IFixitGuideMetadata:
        difficulty = item.get("difficulty")
        if isinstance(difficulty, dict):
            difficulty_name = _to_string(difficulty.get("name"))
        else:
            difficulty_name = _to_string(difficulty)

        return cls(
            guide_id=_to_integer(item.get("guideid") or item.get("id")),
            title=_to_string(item.get("title")) or "",
            category=_to_string(item.get("category") or item.get("device")),
            subject=_to_string(item.get("subject")),
            guide_type=_to_string(item.get("type")),
            url=_to_http_url(item.get("url")),
            locale=_to_string(item.get("locale") or item.get("langid")),
            author=_to_string(item.get("username")),
            revision_id=_to_integer(item.get("revisionid")),
            modified_date=_to_float(item.get("modified_date")),
            time_required_min=_to_integer(item.get("time_required_min")),
            time_required_max=_to_integer(item.get("time_required_max")),
            difficulty=difficulty_name,
        )

    def to_api_dict(self) -> dict[str, object]:
        return asdict(self)


def _to_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _to_integer(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value) if value.is_integer() else None

    if not isinstance(value, str):
        return None

    try:
        return int(value)
    except TypeError, ValueError:
        return None


def _to_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        return float(value)

    if not isinstance(value, str):
        return None

    try:
        return float(value)
    except TypeError, ValueError:
        return None


def _to_http_url(value: object) -> str | None:
    normalized = _to_string(value)
    if normalized and normalized.startswith(("https://", "http://")):
        return normalized
    return None

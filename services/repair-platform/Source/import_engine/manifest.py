"""Structured import manifest and state definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ImportState(StrEnum):
    """Closed set of shadow-import lifecycle states."""

    CREATED = "CREATED"
    HASH_VERIFIED = "HASH_VERIFIED"
    WORKBOOK_VALIDATED = "WORKBOOK_VALIDATED"
    MANIFEST_BUILT = "MANIFEST_BUILT"
    IMPORTING = "IMPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(frozen=True, slots=True)
class ValidationSummary:
    """Machine-readable validation result."""

    result: str
    checks_passed: int
    checks_failed: int
    messages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RollbackMetadata:
    """Rollback information retained without enabling production activation."""

    supported: bool
    strategy: str
    prior_release_id: str | None
    rollback_token: str


@dataclass(frozen=True, slots=True)
class ImportManifest:
    """Immutable release manifest emitted by the import engine."""

    manifest_schema_version: str
    contract_version: str
    release_id: str
    workbook_path: str
    workbook_version: str
    workbook_sha256: str
    imported_at_utc: str
    import_status: ImportState
    row_counts: dict[str, int]
    reconciliation_counts: dict[str, int]
    validation_summary: ValidationSummary
    imported_worksheets: tuple[str, ...]
    rollback_metadata: RollbackMetadata
    activation_allowed: bool = False
    runtime_records_activated: int = 0
    manifest_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        payload = asdict(self)
        payload["import_status"] = self.import_status.value
        return payload

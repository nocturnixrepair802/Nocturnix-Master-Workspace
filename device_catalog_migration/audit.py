"""Audit dataclasses and report structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EntityRecord:
    """A row from a source or target device-related table."""

    entity_type: str
    record_id: str
    values: dict[str, Any]
    worksheet: str
    table_name: str
    row_number: int


@dataclass(slots=True)
class SourceTable:
    """Discovered Excel table metadata."""

    entity_type: str
    worksheet: str
    table_name: str
    ref: str
    header_row: int
    first_data_row: int
    last_data_row: int
    row_count: int
    columns: dict[str, int]
    authoritative: bool = False
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CellChange:
    """A planned or applied workbook cell change."""

    timestamp_utc: str
    worksheet: str
    table_name: str
    cell: str
    row_number: int
    entity_type: str
    record_id: str
    column_name: str
    old_value: Any
    new_value: Any
    match_method: str
    change_reason: str


@dataclass(slots=True)
class ValidationIssue:
    """A validation issue or warning."""

    rule: str
    entity_type: str
    record_id: str
    referenced_id: str
    result: str
    details: str


@dataclass(slots=True)
class DuplicateIssue:
    """A possible duplicate or collision."""

    entity_type: str
    duplicate_type: str
    canonical_key: str
    record_id1: str
    record_id2: str
    display_value1: str
    display_value2: str
    is_active1: Any
    is_active2: Any
    recommended_action: str


@dataclass(slots=True)
class MigrationResult:
    """Summary counters and emitted audit rows."""

    source_workbook: str
    output_workbook: str
    source_sheet: str
    timestamp_utc: str
    source_sha256: str
    output_sha256: str = ""
    worksheets_inspected: int = 0
    worksheets_updated: int = 0
    cells_changed: int = 0
    formulas_changed: int = 0
    matched_by_id: int = 0
    matched_by_composite: int = 0
    unresolved_records: int = 0
    unknown_ids: int = 0
    validation_result: str = "PASS"

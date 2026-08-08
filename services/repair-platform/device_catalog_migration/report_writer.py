"""Write audit worksheets and external migration reports."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from openpyxl.workbook.workbook import Workbook

from .audit import (
    CellChange,
    DuplicateIssue,
    MigrationResult,
    SourceTable,
    ValidationIssue,
)
from .config import AUDIT_SHEETS, EXCEPTIONS_CSV, LOG_CSV, README_REPORT, REPORT_JSON

SUMMARY_HEADERS = ["Metric", "Result", "Details"]
AUDIT_HEADERS = ["TimestampUTC", "Worksheet", "TableName", "Cell", "RowNumber", "EntityType", "RecordID", "ColumnName", "OldValue", "NewValue", "MatchMethod", "ChangeReason"]
EXCEPTION_HEADERS = ["Worksheet", "TableName", "RowNumber", "EntityType", "RecordID", "Manufacturer", "DeviceFamily", "DeviceModel", "ModelNumber", "ExceptionType", "ExceptionDetails", "SuggestedAction"]
VALIDATION_HEADERS = ["ValidationRule", "EntityType", "RecordID", "ReferencedID", "Result", "Details"]
DUP_HEADERS = ["EntityType", "DuplicateType", "CanonicalKey", "RecordID1", "RecordID2", "DisplayValue1", "DisplayValue2", "IsActive1", "IsActive2", "RecommendedAction"]
INVENTORY_HEADERS = ["EntityType", "Worksheet", "TableName", "HeaderRow", "FirstDataRow", "LastDataRow", "RowCount", "ColumnsDetected", "Authoritative", "Notes"]


def replace_audit_sheets(wb: Workbook, result: MigrationResult, changes: list[CellChange], exceptions: list[list[Any]], validations: list[ValidationIssue], duplicates: list[DuplicateIssue], inventory: list[SourceTable], counts: dict[str, int]) -> None:
    """Create or replace migration audit worksheets at workbook end."""
    for name in AUDIT_SHEETS:
        if name in wb.sheetnames:
            del wb[name]
    summary_rows = [
        ["source workbook", result.source_workbook, ""],
        ["output workbook", result.output_workbook, ""],
        ["source worksheet", result.source_sheet, ""],
        ["processing timestamp UTC", result.timestamp_utc, ""],
        ["source SHA-256", result.source_sha256, ""],
        ["output SHA-256", result.output_sha256, ""],
        ["authoritative Device Type row count", counts.get("DeviceType", 0), ""],
        ["authoritative Manufacturer row count", counts.get("Manufacturer", 0), ""],
        ["authoritative Device Family row count", counts.get("DeviceFamily", 0), ""],
        ["authoritative Device Catalog row count", counts.get("DeviceModel", 0), ""],
        ["worksheets inspected", result.worksheets_inspected, ""],
        ["worksheets updated", result.worksheets_updated, ""],
        ["cells changed", result.cells_changed, ""],
        ["formulas changed", result.formulas_changed, ""],
        ["records matched by ID", result.matched_by_id, ""],
        ["records matched by composite key", result.matched_by_composite, ""],
        ["unresolved records", result.unresolved_records, ""],
        ["unknown IDs", result.unknown_ids, ""],
        ["duplicate warnings", len(duplicates), ""],
        ["relationship errors", sum(1 for v in validations if v.result == "FAIL"), ""],
        ["validation result", result.validation_result, ""],
        ["production authorization", "REVIEW REQUIRED", ""],
    ]
    append_sheet(wb, "Migration Summary", SUMMARY_HEADERS, summary_rows)
    append_sheet(wb, "Migration Audit Log", AUDIT_HEADERS, [[c.timestamp_utc, c.worksheet, c.table_name, c.cell, c.row_number, c.entity_type, c.record_id, c.column_name, c.old_value, c.new_value, c.match_method, c.change_reason] for c in changes])
    append_sheet(wb, "Migration Exceptions", EXCEPTION_HEADERS, exceptions)
    append_sheet(wb, "Relationship Validation", VALIDATION_HEADERS, [[v.rule, v.entity_type, v.record_id, v.referenced_id, v.result, v.details] for v in validations])
    append_sheet(wb, "Duplicate Review", DUP_HEADERS, [[d.entity_type, d.duplicate_type, d.canonical_key, d.record_id1, d.record_id2, d.display_value1, d.display_value2, d.is_active1, d.is_active2, d.recommended_action] for d in duplicates])
    append_sheet(wb, "Source Table Inventory", INVENTORY_HEADERS, [[t.entity_type, t.worksheet, t.table_name, t.header_row, t.first_data_row, t.last_data_row, t.row_count, ", ".join(t.columns), t.authoritative, "; ".join(t.reasons)] for t in inventory])


def append_sheet(wb: Workbook, name: str, headers: list[str], rows: list[list[Any]]) -> None:
    """Append a simple audit worksheet."""
    ws = wb.create_sheet(name)
    ws.append(headers)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "A2"


def write_external_reports(directory: Path, result: MigrationResult, changes: list[CellChange], exceptions: list[list[Any]], validations: list[ValidationIssue], duplicates: list[DuplicateIssue]) -> None:
    """Write JSON, CSV, and Markdown migration reports."""
    directory.mkdir(parents=True, exist_ok=True)
    report = {
        "result": asdict(result),
        "changes": [asdict(c) for c in changes],
        "validation": [asdict(v) for v in validations],
        "duplicates": [asdict(d) for d in duplicates],
        "exception_count": len(exceptions),
    }
    (directory / REPORT_JSON).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    write_csv(directory / LOG_CSV, AUDIT_HEADERS, [[c.timestamp_utc, c.worksheet, c.table_name, c.cell, c.row_number, c.entity_type, c.record_id, c.column_name, c.old_value, c.new_value, c.match_method, c.change_reason] for c in changes])
    write_csv(directory / EXCEPTIONS_CSV, EXCEPTION_HEADERS, exceptions)
    (directory / README_REPORT).write_text(
        f"# Device Catalog Migration\n\nValidation result: {result.validation_result}\n\nProduction authorization: REVIEW REQUIRED\n\nCells changed: {result.cells_changed}\n\nUnresolved records: {result.unresolved_records}\n\nUnknown IDs: {result.unknown_ids}\n",
        encoding="utf-8",
    )


def write_csv(path: Path, headers: list[str], rows: list[list[Any]]) -> None:
    """Write a UTF-8 CSV file."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)

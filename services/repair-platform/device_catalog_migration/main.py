"""Command-line entry point for Nocturnix device catalog migration."""

from __future__ import annotations

import argparse
import hashlib
import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .audit import MigrationResult
from .config import OUTPUT_XLSX
from .relationship_engine import (
    build_maps,
    detect_duplicates,
    read_records,
    validate_records,
)
from .report_writer import replace_audit_sheets, write_external_reports
from .sheet_updater import apply_changes, plan_updates
from .validation import scan_ref_errors, validate_reopen, validation_result
from .workbook_discovery import (
    find_authoritative,
    inventory_tables,
    load,
    print_inspection,
)


def sha256(path: Path) -> str:
    """Calculate a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Normalize Nocturnix device-related workbook tables.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", default=OUTPUT_XLSX, type=Path)
    parser.add_argument("--source-sheet", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report-directory", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--inspect-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run the migration."""
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    input_path = args.input.resolve()
    if not input_path.exists():
        raise SystemExit(f"Input workbook not found: {input_path}")
    output_path = args.output.resolve()
    report_dir = (args.report_directory or output_path.parent).resolve()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = input_path.with_name(f"{input_path.stem}.backup_{timestamp}{input_path.suffix}")
    source_hash = sha256(input_path)
    wb = load(input_path)
    original_sheet_names = list(wb.sheetnames)
    original_table_names = {table.name for ws in wb.worksheets for table in ws.tables.values()}
    tables = inventory_tables(wb)
    source_sheet = args.source_sheet if args.source_sheet in wb.sheetnames else "15 LL_Device"
    authoritative = find_authoritative(tables, source_sheet)
    print_inspection(wb, tables, authoritative)
    if args.inspect_only:
        wb.close()
        return
    if len(authoritative) < 4:
        raise SystemExit("Could not locate all four authoritative device tables.")
    shutil.copy2(input_path, backup_path)
    records = read_records(wb, authoritative)
    maps = build_maps(records)
    validations = validate_records(records) + scan_ref_errors(wb)
    duplicates = detect_duplicates(records)
    if args.strict and any(v.result == "FAIL" for v in validations):
        write_external_reports(report_dir, make_result(input_path, output_path, source_sheet, source_hash, timestamp), [], [], validations, duplicates)
        raise SystemExit("Strict mode stopped because authoritative validation failed.")
    changes, exceptions, updated_sheets, matched_by_id, unknown_ids = plan_updates(wb, maps, source_sheet)
    result = make_result(input_path, output_path, source_sheet, source_hash, timestamp)
    result.worksheets_inspected = len(wb.worksheets)
    result.worksheets_updated = len(updated_sheets)
    result.cells_changed = len(changes)
    result.matched_by_id = matched_by_id
    result.unresolved_records = len([e for e in exceptions if e[9] == "UNRESOLVED"])
    result.unknown_ids = unknown_ids
    result.validation_result = validation_result(validations, result.unresolved_records, len(duplicates))
    counts = {entity: len(rows) for entity, rows in records.items()}
    if args.dry_run:
        write_external_reports(report_dir, result, changes, exceptions, validations, duplicates)
        print_summary(result, counts, len(duplicates), len([v for v in validations if v.result == "FAIL"]))
        wb.close()
        return
    apply_changes(wb, changes)
    replace_audit_sheets(wb, result, changes, exceptions, validations, duplicates, tables, counts)
    temp_path = output_path.with_suffix(".tmp.xlsx")
    wb.save(temp_path)
    wb.close()
    reopened_issues = validate_reopen(temp_path, original_sheet_names + [s for s in ["Migration Summary", "Migration Audit Log", "Migration Exceptions", "Relationship Validation", "Duplicate Review", "Source Table Inventory"]], original_table_names)
    validations.extend(reopened_issues)
    result.validation_result = validation_result(validations, result.unresolved_records, len(duplicates))
    if temp_path.exists():
        if output_path.exists():
            output_path.unlink()
        temp_path.rename(output_path)
    result.output_sha256 = sha256(output_path)
    wb2 = load(output_path)
    replace_audit_sheets(wb2, result, changes, exceptions, validations, duplicates, tables, counts)
    wb2.save(output_path)
    wb2.close()
    result.output_sha256 = sha256(output_path)
    write_external_reports(report_dir, result, changes, exceptions, validations, duplicates)
    print_summary(result, counts, len(duplicates), len([v for v in validations if v.result == "FAIL"]))


def make_result(input_path: Path, output_path: Path, source_sheet: str, source_hash: str, timestamp: str) -> MigrationResult:
    """Create a base migration result."""
    return MigrationResult(str(input_path), str(output_path), source_sheet, timestamp, source_hash)


def print_summary(result: MigrationResult, counts: dict[str, int], warnings: int, errors: int) -> None:
    """Print the required concise console summary."""
    print("\nMigration completed")
    print(f"Input: {result.source_workbook}")
    print(f"Output: {result.output_workbook}")
    print(f"Source sheet: {result.source_sheet}")
    print(f"Device Types: {counts.get('DeviceType', 0)}")
    print(f"Manufacturers: {counts.get('Manufacturer', 0)}")
    print(f"Device Families: {counts.get('DeviceFamily', 0)}")
    print(f"Device Models: {counts.get('DeviceModel', 0)}")
    print(f"Worksheets inspected: {result.worksheets_inspected}")
    print(f"Worksheets updated: {result.worksheets_updated}")
    print(f"Cells changed: {result.cells_changed}")
    print(f"Unresolved records: {result.unresolved_records}")
    print(f"Warnings: {warnings}")
    print(f"Errors: {errors}")
    print(f"Validation result: {result.validation_result}")
    print("Production authorization: REVIEW REQUIRED")


if __name__ == "__main__":
    main()

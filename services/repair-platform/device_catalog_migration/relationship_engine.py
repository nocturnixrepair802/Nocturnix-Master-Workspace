"""Build canonical maps and relationship checks."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from openpyxl.workbook.workbook import Workbook

from .audit import DuplicateIssue, EntityRecord, SourceTable, ValidationIssue
from .config import ENTITY_SPECS
from .normalization import normalize_text, valid_id
from .table_reader import row_values


def read_records(wb: Workbook, tables: dict[str, SourceTable]) -> dict[str, dict[str, EntityRecord]]:
    """Read authoritative records by entity and ID."""
    records: dict[str, dict[str, EntityRecord]] = {}
    for entity, table in tables.items():
        ws = wb[table.worksheet]
        id_key = ENTITY_SPECS[entity]["id"]
        entity_records: dict[str, EntityRecord] = {}
        for row in range(table.first_data_row, table.last_data_row + 1):
            values = row_values(ws, row, table.columns)
            record_id = str(values.get(id_key) or "").strip()
            if record_id:
                entity_records[record_id] = EntityRecord(entity, record_id, values, table.worksheet, table.table_name, row)
        records[entity] = entity_records
    manufacturers_by_name = {
        normalize_text(record.values.get("manufacturer")): record_id
        for record_id, record in records.get("Manufacturer", {}).items()
        if normalize_text(record.values.get("manufacturer"))
    }
    for record in records.get("DeviceFamily", {}).values():
        manufacturer_id = str(record.values.get("manufacturerid") or "").strip()

        if (
            not manufacturer_id
            or manufacturer_id.startswith("=")
            or "_xlfn." in manufacturer_id
        ) and record.values.get("manufacturer"):
            resolved_manufacturer_id = manufacturers_by_name.get(
                normalize_text(record.values.get("manufacturer"))
            )
            if resolved_manufacturer_id:
                record.values["manufacturerid"] = resolved_manufacturer_id
    return records


def validate_records(records: dict[str, dict[str, EntityRecord]]) -> list[ValidationIssue]:
    """Validate authoritative IDs and foreign keys."""
    issues: list[ValidationIssue] = []
    for entity, rows in records.items():
        for record_id, record in rows.items():
            if not valid_id(entity, record_id):
                issues.append(ValidationIssue("ID format", entity, record_id, "", "FAIL", "ID does not match expected format"))
            for required in ENTITY_SPECS[entity]["required"]:
                if record.values.get(required) in (None, ""):
                    issues.append(ValidationIssue("Required value", entity, record_id, "", "FAIL", f"{required} is blank"))
    for record_id, record in records.get("DeviceFamily", {}).items():
        manufacturer_id = str(record.values.get("manufacturerid") or "").strip()
        type_id = str(record.values.get("devicetypeid") or "").strip()
        if manufacturer_id and manufacturer_id not in records.get("Manufacturer", {}):
            issues.append(ValidationIssue("Family manufacturer FK", "DeviceFamily", record_id, manufacturer_id, "FAIL", "ManufacturerID not found"))
        if type_id and type_id not in records.get("DeviceType", {}):
            issues.append(ValidationIssue("Family type FK", "DeviceFamily", record_id, type_id, "FAIL", "DeviceTypeID not found"))
    for record_id, record in records.get("DeviceModel", {}).items():
        family_id = str(record.values.get("devicefamilyid") or "").strip()
        if family_id and family_id not in records.get("DeviceFamily", {}):
            issues.append(ValidationIssue("Model family FK", "DeviceModel", record_id, family_id, "FAIL", "DeviceFamilyID not found"))
        family = records.get("DeviceFamily", {}).get(family_id)
        manufacturer_id = str(record.values.get("manufacturerid") or "").strip()
        type_id = str(record.values.get("devicetypeid") or "").strip()
        if manufacturer_id and manufacturer_id not in records.get("Manufacturer", {}):
            issues.append(ValidationIssue("Model manufacturer FK", "DeviceModel", record_id, manufacturer_id, "FAIL", "ManufacturerID not found"))
        if type_id and type_id not in records.get("DeviceType", {}):
            issues.append(ValidationIssue("Model type FK", "DeviceModel", record_id, type_id, "FAIL", "DeviceTypeID not found"))
        if family and family.values.get("manufacturerid") and manufacturer_id and manufacturer_id != family.values.get("manufacturerid"):
            issues.append(ValidationIssue("Model/family manufacturer agreement", "DeviceModel", record_id, manufacturer_id, "FAIL", f"Family {family_id} uses {family.values.get('manufacturerid')}"))
    return issues


def build_maps(records: dict[str, dict[str, EntityRecord]]) -> dict[str, Any]:
    """Build forward and reverse lookup maps."""
    maps: dict[str, Any] = {"records": records}
    maps["device_type_id_by_name"] = {
        normalize_text(r.values.get("devicetype")): rid for rid, r in records.get("DeviceType", {}).items() if normalize_text(r.values.get("devicetype"))
    }
    maps["manufacturer_id_by_name"] = {
        normalize_text(r.values.get("manufacturer")): rid for rid, r in records.get("Manufacturer", {}).items() if normalize_text(r.values.get("manufacturer"))
    }
    maps["family_id_by_key"] = {
        f"{normalize_text(r.values.get('manufacturerid'))}|{normalize_text(r.values.get('devicefamily'))}": rid
        for rid, r in records.get("DeviceFamily", {}).items()
        if normalize_text(r.values.get("devicefamily"))
    }
    maps["model_id_by_key"] = {
        f"{normalize_text(r.values.get('devicefamilyid'))}|{normalize_text(r.values.get('devicemodel'))}": rid
        for rid, r in records.get("DeviceModel", {}).items()
        if normalize_text(r.values.get("devicemodel"))
    }
    maps["model_id_by_number"] = {
        f"{normalize_text(r.values.get('manufacturerid'))}|{normalize_text(r.values.get('modelnumber'))}": rid
        for rid, r in records.get("DeviceModel", {}).items()
        if normalize_text(r.values.get("modelnumber"))
    }
    return maps


def detect_duplicates(records: dict[str, dict[str, EntityRecord]]) -> list[DuplicateIssue]:
    """Detect possible duplicate authoritative records."""
    issues: list[DuplicateIssue] = []

    def add_group(entity: str, duplicate_type: str, items: list[tuple[str, str, EntityRecord]]) -> None:
        for index in range(len(items)):
            for other in range(index + 1, len(items)):
                key, rid1, rec1 = items[index]
                _, rid2, rec2 = items[other]
                issues.append(DuplicateIssue(entity, duplicate_type, key, rid1, rid2, str(rec1.values), str(rec2.values), rec1.values.get("isactive"), rec2.values.get("isactive"), "Review manually; records retained"))

    groups: dict[tuple[str, str], list[tuple[str, str, EntityRecord]]] = defaultdict(list)
    for entity, rows in records.items():
        for rid, rec in rows.items():
            if entity == "DeviceType":
                key = normalize_text(rec.values.get("devicetype"))
            elif entity == "Manufacturer":
                key = normalize_text(rec.values.get("manufacturer"))
            elif entity == "DeviceFamily":
                key = f"{normalize_text(rec.values.get('manufacturerid'))}|{normalize_text(rec.values.get('devicefamily'))}"
            else:
                model_name = normalize_text(rec.values.get("devicemodel"))
                key = f"{normalize_text(rec.values.get('devicefamilyid'))}|{model_name}" if model_name else ""
            if key:
                groups[(entity, key)].append((key, rid, rec))
    for (entity, key), items in groups.items():
        if len(items) > 1:
            add_group(entity, "NORMALIZED_NAME_DUPLICATE", items)
    model_numbers: dict[str, list[tuple[str, str, EntityRecord]]] = defaultdict(list)
    for rid, rec in records.get("DeviceModel", {}).items():
        key = f"{normalize_text(rec.values.get('manufacturerid'))}|{normalize_text(rec.values.get('modelnumber'))}"
        if key.strip("|"):
            model_numbers[key].append((key, rid, rec))
    for key, items in model_numbers.items():
        if len(items) > 1:
            add_group("DeviceModel", "MODEL_NUMBER_COLLISION", items)
    return issues

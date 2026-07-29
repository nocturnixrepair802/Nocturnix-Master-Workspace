from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.database import Database
from core.xlsx_preview import SheetPreview, read_workbook, read_workbook_preview


class ImportService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def inspect_xlsx(self, path: Path) -> tuple[list[SheetPreview], int]:
        previews = read_workbook_preview(path)
        row_count = sum(max(len(sheet.rows) - 1, 0) for sheet in previews)
        self._record_run(path, "xlsx-preview", "inspected", row_count,
                         f"Inspected {len(previews)} worksheet(s); no source file was modified.")
        return previews, row_count

    def import_master_data(self, pricing_path: Path, device_path: Path) -> dict[str, int]:
        pricing = {s.name: s.rows for s in read_workbook(pricing_path)}
        devices = {s.name: s.rows for s in read_workbook(device_path)}

        device_rows = self._records(devices.get("DeviceCatalogTable", []))
        service_rows = self._records(devices.get("Service Catalog", []))
        pricing_rows = self._records(pricing.get("21 - Pricing Output", []))
        pricing_by_service = {r.get("Service ID", ""): r for r in pricing_rows}
        now = datetime.now(timezone.utc).isoformat()

        if not device_rows:
            raise ValueError("DeviceCatalogTable was not found or contained no records.")
        if not service_rows:
            raise ValueError("Service Catalog was not found or contained no records.")

        with self.database.connect() as connection:
            connection.execute("BEGIN")
            connection.execute("DELETE FROM integration_map")
            connection.execute("DELETE FROM pricing_records")
            connection.execute("DELETE FROM services")
            connection.execute("DELETE FROM devices")

            device_count = 0
            for row in device_rows:
                device_id = row.get("DeviceCatalogID", "").strip()
                model = row.get("DeviceModel", "").strip()
                if not device_id or not model:
                    continue
                active = 0 if row.get("ForeignKeyReviewStatus", "").lower().startswith("inactive") else 1
                connection.execute(
                    """INSERT INTO devices(device_id, manufacturer_id, manufacturer, device_family_id,
                       device_type_id, model, active) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (device_id, row.get("ManufacturerID"), row.get("Manufacturer"),
                     row.get("DeviceFamilyID"), row.get("DeviceTypeID"), model, active),
                )
                device_count += 1

            service_count = 0
            pricing_count = 0
            for row in service_rows:
                service_id = row.get("ServiceTypeID", "").strip()
                device_id = row.get("DeviceID", "").strip()
                name = row.get("Service Name", "").strip()
                service_type_id = row.get("Service Type ID", "").strip()
                service_type = row.get("Service Type", "").strip()
                if not service_id or not device_id or not name:
                    continue
                connection.execute(
                    """INSERT INTO services(service_id, internal_name, public_name, service_type_id,
                       service_type_name, active) VALUES (?, ?, ?, ?, ?, 1)""",
                    (service_id, name, name, service_type_id, service_type),
                )
                service_count += 1
                output = pricing_by_service.get(service_id, {})
                part_cost = self._money_to_cents(row.get("Part Cost Input", ""))
                retail = self._money_to_cents(output.get("Recommended Retail", ""))
                status = "needs_cost" if part_cost is None else "draft"
                connection.execute(
                    """INSERT INTO pricing_records(pricing_record_id, device_id, service_id,
                       part_cost_cents, retail_price_cents, approval_status, public_approved,
                       square_approved, updated_at) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)""",
                    (f"PR-{service_id}", device_id, service_id, part_cost, retail, status, now),
                )
                connection.execute(
                    "INSERT INTO integration_map(pricing_record_id) VALUES (?)",
                    (f"PR-{service_id}",),
                )
                pricing_count += 1

            connection.commit()

        total = device_count + service_count + pricing_count
        self._record_run(pricing_path, "master-import", "completed", total,
                         f"Imported {device_count} devices, {service_count} services, and {pricing_count} pricing records.")
        return {"devices": device_count, "services": service_count, "pricing": pricing_count}

    @staticmethod
    def _records(rows: list[list[str]]) -> list[dict[str, str]]:
        if not rows:
            return []
        headers = [str(h).strip() for h in rows[0]]
        records: list[dict[str, str]] = []
        for values in rows[1:]:
            record = {header: (values[i] if i < len(values) else "") for i, header in enumerate(headers) if header}
            if any(str(value).strip() for value in record.values()):
                records.append(record)
        return records

    @staticmethod
    def _money_to_cents(value: str) -> int | None:
        text = str(value).strip().replace("$", "").replace(",", "")
        if not text:
            return None
        try:
            return round(float(text) * 100)
        except ValueError:
            return None

    def _record_run(self, path: Path, source_type: str, status: str, row_count: int, notes: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO import_runs(source_path, source_type, imported_at, status, row_count, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(path), source_type, datetime.now(timezone.utc).isoformat(), status, row_count, notes),
            )

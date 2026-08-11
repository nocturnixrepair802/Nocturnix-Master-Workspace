from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RepairService:
    BACKUP_LIMIT = 10

    def __init__(self) -> None:
        self.database_path = self._resolve_database_path()
        self.backup_directory = self.database_path.parent / "backups"

        self.backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.create_startup_backup()

    @staticmethod
    def _resolve_database_path() -> Path:
        service_root = Path(__file__).resolve().parents[3]

        return service_root / "data" / "nocturnix_operations.sqlite3"

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("PRAGMA journal_mode = WAL")

        return connection

    def create_startup_backup(self) -> Path | None:
        if not self.database_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")

        backup_path = (
            self.backup_directory / f"nocturnix_operations-{timestamp}.sqlite3"
        )

        source = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        destination = sqlite3.connect(
            backup_path,
            timeout=30,
        )

        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        self._prune_backups()

        return backup_path

    def create_write_backup(self) -> Path | None:
        return self.create_startup_backup()

    def _prune_backups(self) -> None:
        backups = sorted(
            self.backup_directory.glob("nocturnix_operations-*.sqlite3"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[self.BACKUP_LIMIT :]:
            old_backup.unlink(missing_ok=True)

    @staticmethod
    def _optional_float(
        value: object,
    ) -> float | None:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"Invalid currency amount: {text}") from exc

    # ---------------------------------------------------------
    # DASHBOARD
    # ---------------------------------------------------------

    def dashboard_counts(self) -> dict[str, int]:
        with self.connect() as connection:
            customers = connection.execute("""
                SELECT COUNT(*)
                FROM customers
                """).fetchone()[0]

            devices = connection.execute("""
                SELECT COUNT(*)
                FROM customer_devices
                """).fetchone()[0]

            repairs = connection.execute("""
                SELECT COUNT(*)
                FROM repair_tickets
                """).fetchone()[0]

            open_repairs = connection.execute("""
                SELECT COUNT(*)
                FROM repair_tickets
                WHERE repair_status NOT IN (
                    'Completed',
                    'Picked Up',
                    'Cancelled'
                )
                """).fetchone()[0]

        return {
            "customers": int(customers),
            "devices": int(devices),
            "repairs": int(repairs),
            "open_repairs": int(open_repairs),
        }

    def dashboard_operational_counts(
        self,
    ) -> dict[str, int]:
        with self.connect() as connection:
            row = connection.execute("""
                SELECT
                    SUM(
                        CASE
                            WHEN repair_status =
                                'Awaiting Diagnosis'
                            THEN 1
                            ELSE 0
                        END
                    ) AS awaiting_diagnosis,

                    SUM(
                        CASE
                            WHEN repair_status =
                                'Awaiting Approval'
                            THEN 1
                            ELSE 0
                        END
                    ) AS awaiting_approval,

                    SUM(
                        CASE
                            WHEN repair_status =
                                'In Repair'
                            THEN 1
                            ELSE 0
                        END
                    ) AS in_repair,

                    SUM(
                        CASE
                            WHEN repair_status =
                                'Awaiting Parts'
                            THEN 1
                            ELSE 0
                        END
                    ) AS awaiting_parts,

                    SUM(
                        CASE
                            WHEN repair_status =
                                'Ready for Pickup'
                            THEN 1
                            ELSE 0
                        END
                    ) AS ready_for_pickup,

                    SUM(
                        CASE
                            WHEN priority = 'Urgent'
                            AND repair_status NOT IN (
                                'Completed',
                                'Picked Up',
                                'Cancelled'
                            )
                            THEN 1
                            ELSE 0
                        END
                    ) AS urgent_repairs

                FROM repair_tickets
                """).fetchone()

        if row is None:
            return {
                "awaiting_diagnosis": 0,
                "awaiting_approval": 0,
                "in_repair": 0,
                "awaiting_parts": 0,
                "ready_for_pickup": 0,
                "urgent_repairs": 0,
            }

        return {
            "awaiting_diagnosis": int(row["awaiting_diagnosis"] or 0),
            "awaiting_approval": int(row["awaiting_approval"] or 0),
            "in_repair": int(row["in_repair"] or 0),
            "awaiting_parts": int(row["awaiting_parts"] or 0),
            "ready_for_pickup": int(row["ready_for_pickup"] or 0),
            "urgent_repairs": int(row["urgent_repairs"] or 0),
        }

    def recent_repair_activity(
        self,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.event_id,
                    e.repair_id,
                    e.event_type,
                    e.old_value,
                    e.new_value,
                    e.notes,
                    e.created_at,

                    r.repair_status,

                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    c.business_name,

                    d.device_id,
                    d.manufacturer,
                    d.device_family,
                    d.device_model,
                    d.serial_number

                FROM repair_events AS e

                JOIN repair_tickets AS r
                    ON r.ticket_id =
                       e.repair_id

                JOIN customers AS c
                    ON c.customer_id =
                       r.customer_id

                JOIN customer_devices AS d
                    ON d.device_id =
                       r.device_id

                ORDER BY
                    e.created_at DESC

                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # CUSTOMERS
    # ---------------------------------------------------------

    def list_customers(
        self,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    customer_id,
                    first_name,
                    last_name,
                    business_name,
                    email,
                    mobile_phone,
                    customer_type,
                    active
                FROM customers
                ORDER BY
                    last_name COLLATE NOCASE,
                    first_name COLLATE NOCASE,
                    business_name COLLATE NOCASE
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_customer(
        self,
        customer_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def _next_customer_id(self) -> str:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT customer_id
                FROM customers
                """).fetchall()

        highest = 0

        for row in rows:
            customer_id = str(row["customer_id"])

            match = re.fullmatch(
                r"CUS(\d{6})",
                customer_id,
            )

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"CUS{highest + 1:06d}"

    @staticmethod
    def _normalize_customer_values(
        values: dict[str, Any],
    ) -> dict[str, Any]:
        customer_type = str(
            values.get(
                "customer_type",
                "Individual",
            )
        ).strip()

        first_name = str(
            values.get(
                "first_name",
                "",
            )
        ).strip()

        last_name = str(
            values.get(
                "last_name",
                "",
            )
        ).strip()

        business_name = str(
            values.get(
                "business_name",
                "",
            )
        ).strip()

        if customer_type == "Business":
            if not business_name:
                raise ValueError(
                    "Business Name is required " "for a Business customer."
                )

        elif not first_name and not last_name:
            raise ValueError("Enter a first name or last name.")

        return {
            "customer_type": customer_type,
            "first_name": first_name,
            "last_name": last_name,
            "business_name": business_name,
            "email": str(
                values.get(
                    "email",
                    "",
                )
            ).strip(),
            "mobile_phone": str(
                values.get(
                    "mobile_phone",
                    "",
                )
            ).strip(),
            "home_phone": str(
                values.get(
                    "home_phone",
                    "",
                )
            ).strip(),
            "work_phone": str(
                values.get(
                    "work_phone",
                    "",
                )
            ).strip(),
            "preferred_contact": str(
                values.get(
                    "preferred_contact",
                    "Mobile Phone",
                )
            ).strip(),
            "billing_address": str(
                values.get(
                    "billing_address",
                    "",
                )
            ).strip(),
            "shipping_address": str(
                values.get(
                    "shipping_address",
                    "",
                )
            ).strip(),
            "tax_exempt": 1 if values.get("tax_exempt") else 0,
            "active": (
                1
                if values.get(
                    "active",
                    True,
                )
                else 0
            ),
            "notes": str(
                values.get(
                    "notes",
                    "",
                )
            ).strip(),
        }

    def create_customer(
        self,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = self._normalize_customer_values(values)

        customer_id = self._next_customer_id()

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO customers (
                    customer_id,
                    customer_type,
                    first_name,
                    last_name,
                    business_name,
                    email,
                    mobile_phone,
                    home_phone,
                    work_phone,
                    preferred_contact,
                    billing_address,
                    shipping_address,
                    tax_exempt,
                    active,
                    date_created,
                    last_modified,
                    notes
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    customer_id,
                    normalized["customer_type"],
                    normalized["first_name"],
                    normalized["last_name"],
                    normalized["business_name"],
                    normalized["email"],
                    normalized["mobile_phone"],
                    normalized["home_phone"],
                    normalized["work_phone"],
                    normalized["preferred_contact"],
                    normalized["billing_address"],
                    normalized["shipping_address"],
                    normalized["tax_exempt"],
                    normalized["active"],
                    now,
                    now,
                    normalized["notes"],
                ),
            )

            connection.commit()

        customer = self.get_customer(customer_id)

        if customer is None:
            raise RuntimeError("Customer was created but " "could not be reloaded.")

        return customer

    def update_customer(
        self,
        customer_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        if self.get_customer(customer_id) is None:
            raise ValueError(f"Customer not found: " f"{customer_id}")

        normalized = self._normalize_customer_values(values)

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE customers
                SET
                    customer_type = ?,
                    first_name = ?,
                    last_name = ?,
                    business_name = ?,
                    email = ?,
                    mobile_phone = ?,
                    home_phone = ?,
                    work_phone = ?,
                    preferred_contact = ?,
                    billing_address = ?,
                    shipping_address = ?,
                    tax_exempt = ?,
                    active = ?,
                    last_modified = ?,
                    notes = ?
                WHERE customer_id = ?
                """,
                (
                    normalized["customer_type"],
                    normalized["first_name"],
                    normalized["last_name"],
                    normalized["business_name"],
                    normalized["email"],
                    normalized["mobile_phone"],
                    normalized["home_phone"],
                    normalized["work_phone"],
                    normalized["preferred_contact"],
                    normalized["billing_address"],
                    normalized["shipping_address"],
                    normalized["tax_exempt"],
                    normalized["active"],
                    now,
                    normalized["notes"],
                    customer_id,
                ),
            )

            connection.commit()

        customer = self.get_customer(customer_id)

        if customer is None:
            raise RuntimeError("Customer was updated but " "could not be reloaded.")

        return customer

    # ---------------------------------------------------------
    # DEVICES
    # ---------------------------------------------------------

    def list_all_devices(
        self,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT
                    d.device_id,
                    d.customer_id,
                    d.manufacturer,
                    d.device_family,
                    d.device_model,
                    d.serial_number,
                    d.imei_service_tag,
                    d.color,
                    d.storage,
                    d.carrier,
                    d.purchase_date,
                    d.warranty_expiration,
                    d.active,
                    d.notes,
                    d.catalog_device_id,

                    c.first_name,
                    c.last_name,
                    c.business_name

                FROM customer_devices AS d

                JOIN customers AS c
                    ON c.customer_id =
                       d.customer_id

                ORDER BY
                    d.manufacturer
                        COLLATE NOCASE,
                    d.device_model
                        COLLATE NOCASE,
                    d.device_id
                """).fetchall()

        return [dict(row) for row in rows]

    def list_customer_devices(
        self,
        customer_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    device_id,
                    customer_id,
                    manufacturer,
                    device_family,
                    device_model,
                    serial_number,
                    imei_service_tag,
                    color,
                    storage,
                    carrier,
                    purchase_date,
                    warranty_expiration,
                    active,
                    notes,
                    catalog_device_id
                FROM customer_devices
                WHERE customer_id = ?
                ORDER BY
                    manufacturer
                        COLLATE NOCASE,
                    device_family
                        COLLATE NOCASE,
                    device_model
                        COLLATE NOCASE,
                    device_id
                """,
                (customer_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_device(
        self,
        device_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM customer_devices
                WHERE device_id = ?
                """,
                (device_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def _next_device_id(self) -> str:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT device_id
                FROM customer_devices
                """).fetchall()

        highest = 0

        for row in rows:
            device_id = str(row["device_id"])

            match = re.fullmatch(
                r"CDEV(\d{6})",
                device_id,
            )

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"CDEV{highest + 1:06d}"

    def create_device(
        self,
        customer_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        customer = self.get_customer(customer_id)

        if customer is None:
            raise ValueError(f"Customer not found: " f"{customer_id}")

        manufacturer = str(
            values.get(
                "manufacturer",
                "",
            )
        ).strip()

        device_family = str(
            values.get(
                "device_family",
                "",
            )
        ).strip()

        device_model = str(
            values.get(
                "device_model",
                "",
            )
        ).strip()

        serial_number = str(
            values.get(
                "serial_number",
                "",
            )
        ).strip()

        imei_service_tag = str(
            values.get(
                "imei_service_tag",
                "",
            )
        ).strip()

        color = str(
            values.get(
                "color",
                "",
            )
        ).strip()

        storage = str(
            values.get(
                "storage",
                "",
            )
        ).strip()

        carrier = str(
            values.get(
                "carrier",
                "",
            )
        ).strip()

        purchase_date = str(
            values.get(
                "purchase_date",
                "",
            )
        ).strip()

        warranty_expiration = str(
            values.get(
                "warranty_expiration",
                "",
            )
        ).strip()

        notes = str(
            values.get(
                "notes",
                "",
            )
        ).strip()

        catalog_device_id = str(
            values.get(
                "catalog_device_id",
                "",
            )
        ).strip()

        active = (
            1
            if values.get(
                "active",
                True,
            )
            else 0
        )

        if not manufacturer:
            raise ValueError("Manufacturer is required.")

        if not (device_family or device_model or serial_number or imei_service_tag):
            raise ValueError(
                "Enter a device family, model, "
                "serial number, or "
                "IMEI/service tag."
            )

        device_id = self._next_device_id()

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO customer_devices (
                    device_id,
                    customer_id,
                    manufacturer,
                    device_family,
                    device_model,
                    serial_number,
                    imei_service_tag,
                    color,
                    storage,
                    carrier,
                    purchase_date,
                    warranty_expiration,
                    active,
                    notes,
                    catalog_device_id
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    device_id,
                    customer_id,
                    manufacturer,
                    device_family,
                    device_model,
                    serial_number,
                    imei_service_tag,
                    color,
                    storage,
                    carrier,
                    purchase_date or None,
                    (warranty_expiration or None),
                    active,
                    notes,
                    catalog_device_id,
                ),
            )

            connection.commit()

        device = self.get_device(device_id)

        if device is None:
            raise RuntimeError("Device was created but " "could not be reloaded.")

        return device

    def update_device(
        self,
        device_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        current = self.get_device(device_id)

        if current is None:
            raise ValueError(f"Device not found: " f"{device_id}")

        manufacturer = str(
            values.get(
                "manufacturer",
                "",
            )
        ).strip()

        device_family = str(
            values.get(
                "device_family",
                "",
            )
        ).strip()

        device_model = str(
            values.get(
                "device_model",
                "",
            )
        ).strip()

        serial_number = str(
            values.get(
                "serial_number",
                "",
            )
        ).strip()

        imei_service_tag = str(
            values.get(
                "imei_service_tag",
                "",
            )
        ).strip()

        color = str(
            values.get(
                "color",
                "",
            )
        ).strip()

        storage = str(
            values.get(
                "storage",
                "",
            )
        ).strip()

        carrier = str(
            values.get(
                "carrier",
                "",
            )
        ).strip()

        purchase_date = str(
            values.get(
                "purchase_date",
                "",
            )
        ).strip()

        warranty_expiration = str(
            values.get(
                "warranty_expiration",
                "",
            )
        ).strip()

        notes = str(
            values.get(
                "notes",
                "",
            )
        ).strip()

        catalog_device_id = str(
            values.get(
                "catalog_device_id",
                "",
            )
        ).strip()

        active = (
            1
            if values.get(
                "active",
                True,
            )
            else 0
        )

        if not manufacturer:
            raise ValueError("Manufacturer is required.")

        if not (device_family or device_model or serial_number or imei_service_tag):
            raise ValueError(
                "Enter a device family, model, "
                "serial number, or "
                "IMEI/service tag."
            )

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE customer_devices
                SET
                    manufacturer = ?,
                    device_family = ?,
                    device_model = ?,
                    serial_number = ?,
                    imei_service_tag = ?,
                    color = ?,
                    storage = ?,
                    carrier = ?,
                    purchase_date = ?,
                    warranty_expiration = ?,
                    active = ?,
                    notes = ?,
                    catalog_device_id = ?
                WHERE device_id = ?
                """,
                (
                    manufacturer,
                    device_family,
                    device_model,
                    serial_number,
                    imei_service_tag,
                    color,
                    storage,
                    carrier,
                    purchase_date or None,
                    (warranty_expiration or None),
                    active,
                    notes,
                    catalog_device_id,
                    device_id,
                ),
            )

            connection.commit()

        updated = self.get_device(device_id)

        if updated is None:
            raise RuntimeError("Device was updated but " "could not be reloaded.")

        return updated

    # ---------------------------------------------------------
    # REPAIRS / EVENTS
    # ---------------------------------------------------------

    def _next_repair_id(self) -> str:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT ticket_id
                FROM repair_tickets
                """).fetchall()

        highest = 0

        for row in rows:
            ticket_id = str(row["ticket_id"])

            match = re.fullmatch(
                r"RPR(\d{6})",
                ticket_id,
            )

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"RPR{highest + 1:06d}"

    def _next_event_id(self) -> str:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT event_id
                FROM repair_events
                """).fetchall()

        highest = 0

        for row in rows:
            event_id = str(row["event_id"])

            match = re.fullmatch(
                r"EVT(\d{6})",
                event_id,
            )

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"EVT{highest + 1:06d}"

    @staticmethod
    def _insert_repair_event(
        connection: sqlite3.Connection,
        *,
        event_id: str,
        repair_id: str,
        event_type: str,
        old_value: str = "",
        new_value: str = "",
        notes: str = "",
        created_by: str = "Ryan Brown",
    ) -> None:
        created_at = datetime.now(UTC).isoformat()

        connection.execute(
            """
            INSERT INTO repair_events (
                event_id,
                repair_id,
                event_type,
                old_value,
                new_value,
                notes,
                created_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                repair_id,
                event_type,
                old_value,
                new_value,
                notes,
                created_at,
                created_by,
            ),
        )

    def create_repair(
        self,
        customer_id: str,
        device_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        customer = self.get_customer(customer_id)

        if customer is None:
            raise ValueError(f"Customer not found: " f"{customer_id}")

        device = self.get_device(device_id)

        if device is None:
            raise ValueError(f"Device not found: " f"{device_id}")

        if str(device["customer_id"]) != customer_id:
            raise ValueError("The selected device does not " "belong to this customer.")

        repair_status = str(
            values.get(
                "repair_status",
                "New Intake",
            )
        ).strip()

        technician = str(
            values.get(
                "technician",
                "Ryan Brown",
            )
        ).strip()

        priority = str(
            values.get(
                "priority",
                "Normal",
            )
        ).strip()

        due_date = str(
            values.get(
                "due_date",
                "",
            )
        ).strip()

        problem_description = str(
            values.get(
                "problem_description",
                "",
            )
        ).strip()

        diagnosis = str(
            values.get(
                "diagnosis",
                "",
            )
        ).strip()

        notes = str(
            values.get(
                "notes",
                "",
            )
        ).strip()

        warranty = 1 if values.get("warranty") else 0

        estimated_cost = self._optional_float(values.get("estimated_cost"))

        if not problem_description:
            raise ValueError("Problem Description " "is required.")

        if not technician:
            raise ValueError("Technician is required.")

        ticket_id = self._next_repair_id()

        event_id = self._next_event_id()

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO repair_tickets (
                    ticket_id,
                    customer_id,
                    device_id,
                    repair_status,
                    intake_date,
                    technician,
                    priority,
                    due_date,
                    problem_description,
                    diagnosis,
                    estimated_cost,
                    final_cost,
                    date_completed,
                    date_picked_up,
                    warranty,
                    notes,
                    last_modified
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    ticket_id,
                    customer_id,
                    device_id,
                    repair_status,
                    now,
                    technician,
                    priority,
                    due_date,
                    problem_description,
                    diagnosis,
                    estimated_cost,
                    None,
                    None,
                    None,
                    warranty,
                    notes,
                    now,
                ),
            )

            self._insert_repair_event(
                connection,
                event_id=event_id,
                repair_id=ticket_id,
                event_type="repair_created",
                new_value=repair_status,
                notes=problem_description,
                created_by=technician,
            )

            connection.commit()

        repair = self.get_repair(ticket_id)

        if repair is None:
            raise RuntimeError(
                "Repair ticket was created but " "could not be reloaded."
            )

        return repair

    def get_repair(
        self,
        ticket_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_tickets
                WHERE ticket_id = ?
                """,
                (ticket_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_repair_workspace(
        self,
        ticket_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    r.ticket_id,
                    r.customer_id,
                    r.device_id,
                    r.repair_status,
                    r.intake_date,
                    r.technician,
                    r.priority,
                    r.due_date,
                    r.problem_description,
                    r.diagnosis,
                    r.estimated_cost,
                    r.final_cost,
                    r.date_completed,
                    r.date_picked_up,
                    r.warranty,
                    r.notes,
                    r.last_modified,

                    c.customer_type,
                    c.first_name,
                    c.last_name,
                    c.business_name,
                    c.email,
                    c.mobile_phone,
                    c.preferred_contact,

                    d.manufacturer,
                    d.device_family,
                    d.device_model,
                    d.serial_number,
                    d.imei_service_tag,
                    d.color,
                    d.storage,
                    d.carrier,
                    d.catalog_device_id

                FROM repair_tickets AS r

                JOIN customers AS c
                    ON c.customer_id =
                       r.customer_id

                JOIN customer_devices AS d
                    ON d.device_id =
                       r.device_id

                WHERE r.ticket_id = ?
                """,
                (ticket_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def update_repair(
        self,
        ticket_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        current = self.get_repair(ticket_id)

        if current is None:
            raise ValueError(f"Repair not found: " f"{ticket_id}")

        old_status = str(current["repair_status"])

        repair_status = str(
            values.get(
                "repair_status",
                old_status,
            )
        ).strip()

        technician = str(
            values.get(
                "technician",
                current["technician"],
            )
        ).strip()

        priority = str(
            values.get(
                "priority",
                current["priority"],
            )
        ).strip()

        due_date = str(
            values.get(
                "due_date",
                current["due_date"],
            )
            or ""
        ).strip()

        problem_description = str(
            values.get(
                "problem_description",
                current["problem_description"],
            )
        ).strip()

        diagnosis = str(
            values.get(
                "diagnosis",
                current["diagnosis"],
            )
            or ""
        ).strip()

        notes = str(
            values.get(
                "notes",
                current["notes"],
            )
            or ""
        ).strip()

        warranty = 1 if values.get("warranty") else 0

        estimated_cost = self._optional_float(values.get("estimated_cost"))

        final_cost = self._optional_float(values.get("final_cost"))

        if not problem_description:
            raise ValueError("Problem Description is required.")

        if not technician:
            raise ValueError("Technician is required.")

        now = datetime.now(UTC).isoformat()

        status_event_id: str | None = None

        if repair_status != old_status:
            status_event_id = self._next_event_id()

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE repair_tickets
                SET
                    repair_status = ?,
                    technician = ?,
                    priority = ?,
                    due_date = ?,
                    problem_description = ?,
                    diagnosis = ?,
                    estimated_cost = ?,
                    final_cost = ?,
                    warranty = ?,
                    notes = ?,
                    last_modified = ?
                WHERE ticket_id = ?
                """,
                (
                    repair_status,
                    technician,
                    priority,
                    due_date,
                    problem_description,
                    diagnosis,
                    estimated_cost,
                    final_cost,
                    warranty,
                    notes,
                    now,
                    ticket_id,
                ),
            )

            if status_event_id is not None:
                self._insert_repair_event(
                    connection,
                    event_id=status_event_id,
                    repair_id=ticket_id,
                    event_type=("repair_status_changed"),
                    old_value=old_status,
                    new_value=repair_status,
                    notes=("Repair status changed " "from desktop application."),
                    created_by=technician,
                )

            connection.commit()

        updated = self.get_repair(ticket_id)

        if updated is None:
            raise RuntimeError("Repair was updated but " "could not be reloaded.")

        return updated

    def list_repairs(
        self,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    r.ticket_id,
                    r.repair_status,
                    r.intake_date,
                    r.priority,
                    r.technician,
                    r.problem_description,

                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    c.business_name,

                    d.device_id,
                    d.manufacturer,
                    d.device_family,
                    d.device_model,
                    d.serial_number

                FROM repair_tickets AS r

                JOIN customers AS c
                    ON c.customer_id =
                       r.customer_id

                JOIN customer_devices AS d
                    ON d.device_id =
                       r.device_id

                ORDER BY
                    r.intake_date DESC

                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # CHECK-INS
    # ---------------------------------------------------------

    def _next_checkin_id(self) -> str:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT checkin_id
                FROM repair_checkins
                """).fetchall()

        highest = 0

        for row in rows:
            checkin_id = str(row["checkin_id"])

            match = re.fullmatch(
                r"CHK(\d{6})",
                checkin_id,
            )

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"CHK{highest + 1:06d}"

    def create_checkin(
        self,
        repair_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        repair = self.get_repair(repair_id)

        if repair is None:
            raise ValueError(f"Repair not found: " f"{repair_id}")

        customer_id = str(repair["customer_id"])

        device_id = str(repair["device_id"])

        technician = str(
            values.get(
                "technician",
                repair["technician"],
            )
        ).strip()

        if not technician:
            raise ValueError("Technician is required.")

        battery_raw = str(
            values.get(
                "battery_percentage",
                "",
            )
        ).strip()

        battery_percentage: int | None

        if battery_raw:
            try:
                battery_percentage = int(battery_raw)
            except ValueError as exc:
                raise ValueError(
                    "Battery Percentage must " "be a whole number."
                ) from exc

            if not (0 <= battery_percentage <= 100):
                raise ValueError("Battery Percentage must " "be between 0 and 100.")
        else:
            battery_percentage = None

        checkin_id = self._next_checkin_id()

        event_id = self._next_event_id()

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO repair_checkins (
                    checkin_id,
                    repair_id,
                    customer_id,
                    device_id,
                    technician,
                    checkin_timestamp,
                    powers_on,
                    battery_percentage,
                    screen_condition,
                    frame_condition,
                    back_glass_condition,
                    charging_port_condition,
                    camera_condition,
                    speaker_condition,
                    microphone_condition,
                    face_id_touch_id,
                    liquid_damage,
                    existing_damage,
                    accessories_received,
                    device_passcode,
                    passcode_available,
                    intake_notes
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    checkin_id,
                    repair_id,
                    customer_id,
                    device_id,
                    technician,
                    now,
                    str(
                        values.get(
                            "powers_on",
                            "",
                        )
                    ).strip(),
                    battery_percentage,
                    str(
                        values.get(
                            "screen_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "frame_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "back_glass_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "charging_port_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "camera_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "speaker_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "microphone_condition",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "face_id_touch_id",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "liquid_damage",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "existing_damage",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "accessories_received",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "device_passcode",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "passcode_available",
                            "",
                        )
                    ).strip(),
                    str(
                        values.get(
                            "intake_notes",
                            "",
                        )
                    ).strip(),
                ),
            )

            self._insert_repair_event(
                connection,
                event_id=event_id,
                repair_id=repair_id,
                event_type=("checkin_created"),
                new_value=checkin_id,
                notes=("Device check-in created " "from desktop application."),
                created_by=technician,
            )

            connection.commit()

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_checkins
                WHERE checkin_id = ?
                """,
                (checkin_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Check-In was created but " "could not be reloaded.")

        return dict(row)

    def list_checkins(
        self,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    ch.checkin_id,
                    ch.repair_id,
                    ch.checkin_timestamp,
                    ch.technician,
                    ch.powers_on,
                    ch.battery_percentage,
                    ch.liquid_damage,
                    ch.passcode_available,

                    c.first_name,
                    c.last_name,
                    c.business_name,

                    d.manufacturer,
                    d.device_model,
                    d.serial_number

                FROM repair_checkins AS ch

                JOIN customers AS c
                    ON c.customer_id =
                       ch.customer_id

                JOIN customer_devices AS d
                    ON d.device_id =
                       ch.device_id

                ORDER BY
                    ch.checkin_timestamp DESC

                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_repair_checkins(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    checkin_id,
                    repair_id,
                    technician,
                    checkin_timestamp,
                    powers_on,
                    battery_percentage,
                    screen_condition,
                    frame_condition,
                    back_glass_condition,
                    charging_port_condition,
                    camera_condition,
                    speaker_condition,
                    microphone_condition,
                    face_id_touch_id,
                    liquid_damage,
                    existing_damage,
                    accessories_received,
                    passcode_available,
                    intake_notes
                FROM repair_checkins
                WHERE repair_id = ?
                ORDER BY
                    checkin_timestamp DESC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_id,
                    repair_id,
                    event_type,
                    old_value,
                    new_value,
                    notes,
                    created_at,
                    created_by
                FROM repair_events
                WHERE repair_id = ?
                ORDER BY
                    created_at DESC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

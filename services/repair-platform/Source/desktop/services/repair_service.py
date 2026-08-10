from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class RepairService:
    def __init__(self) -> None:
        self.database_path = self._resolve_database_path()

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

        return connection

    def dashboard_counts(self) -> dict[str, int]:
        with self.connect() as connection:
            customers = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[
                0
            ]

            devices = connection.execute(
                "SELECT COUNT(*) FROM customer_devices"
            ).fetchone()[0]

            repairs = connection.execute(
                "SELECT COUNT(*) FROM repair_tickets"
            ).fetchone()[0]

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
                    ON c.customer_id = r.customer_id
                JOIN customer_devices AS d
                    ON d.device_id = r.device_id
                ORDER BY r.intake_date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

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
                    ON c.customer_id = ch.customer_id
                JOIN customer_devices AS d
                    ON d.device_id = ch.device_id
                ORDER BY ch.checkin_timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

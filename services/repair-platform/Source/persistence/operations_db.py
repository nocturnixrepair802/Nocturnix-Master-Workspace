from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


class OperationsDatabase:
    """SQLite-backed operational data store."""

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize()

    def connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("PRAGMA journal_mode = WAL")

        return connection

    def get_wpforms_submission(
        self,
        form_id: str,
        entry_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM wpforms_submissions
                WHERE wpforms_form_id = ?
                  AND wpforms_entry_id = ?
                """,
                (
                    form_id,
                    entry_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def create_wpforms_submission(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO wpforms_submissions (
                    submission_id,
                    wpforms_form_id,
                    wpforms_entry_id,
                    customer_id,
                    device_id,
                    repair_id,
                    checkin_id,
                    received_at
                )
                VALUES (
                    :submission_id,
                    :wpforms_form_id,
                    :wpforms_entry_id,
                    :customer_id,
                    :device_id,
                    :repair_id,
                    :checkin_id,
                    :received_at
                )
                """,
                record,
            )

        return record.copy()

    def initialize(
        self,
    ) -> None:
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    customer_type TEXT NOT NULL,
                    first_name TEXT NOT NULL DEFAULT '',
                    last_name TEXT NOT NULL DEFAULT '',
                    business_name TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    mobile_phone TEXT NOT NULL DEFAULT '',
                    home_phone TEXT NOT NULL DEFAULT '',
                    work_phone TEXT NOT NULL DEFAULT '',
                    preferred_contact TEXT NOT NULL DEFAULT 'Mobile Phone',
                    billing_address TEXT NOT NULL DEFAULT '',
                    shipping_address TEXT NOT NULL DEFAULT '',
                    tax_exempt INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    date_created TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS
                    idx_customers_last_name
                    ON customers(last_name);

                CREATE INDEX IF NOT EXISTS
                    idx_customers_mobile_phone
                    ON customers(mobile_phone);

                CREATE INDEX IF NOT EXISTS
                    idx_customers_email
                    ON customers(email);


                CREATE TABLE IF NOT EXISTS customer_devices (
                    device_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    manufacturer TEXT NOT NULL DEFAULT '',
                    device_family TEXT NOT NULL DEFAULT '',
                    device_model TEXT NOT NULL DEFAULT '',
                    serial_number TEXT NOT NULL DEFAULT '',
                    imei_service_tag TEXT NOT NULL DEFAULT '',
                    color TEXT NOT NULL DEFAULT '',
                    storage TEXT NOT NULL DEFAULT '',
                    carrier TEXT NOT NULL DEFAULT '',
                    purchase_date TEXT,
                    warranty_expiration TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    notes TEXT NOT NULL DEFAULT '',

                    FOREIGN KEY(customer_id)
                        REFERENCES customers(customer_id)
                        ON UPDATE CASCADE
                        ON DELETE RESTRICT
                );

                CREATE INDEX IF NOT EXISTS
                    idx_customer_devices_customer_id
                    ON customer_devices(customer_id);

                CREATE INDEX IF NOT EXISTS
                    idx_customer_devices_serial_number
                    ON customer_devices(serial_number);


                CREATE TABLE IF NOT EXISTS repair_tickets (
                    ticket_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    repair_status TEXT NOT NULL DEFAULT 'New Intake',
                    intake_date TEXT NOT NULL,
                    technician TEXT NOT NULL DEFAULT 'Ryan Brown',
                    priority TEXT NOT NULL DEFAULT 'Normal',
                    due_date TEXT NOT NULL DEFAULT '',
                    problem_description TEXT NOT NULL DEFAULT '',
                    diagnosis TEXT NOT NULL DEFAULT '',
                    estimated_cost REAL,
                    final_cost REAL,
                    date_completed TEXT,
                    date_picked_up TEXT,
                    warranty INTEGER NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    last_modified TEXT NOT NULL,

                    FOREIGN KEY(customer_id)
                        REFERENCES customers(customer_id)
                        ON UPDATE CASCADE
                        ON DELETE RESTRICT,

                    FOREIGN KEY(device_id)
                        REFERENCES customer_devices(device_id)
                        ON UPDATE CASCADE
                        ON DELETE RESTRICT
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_tickets_customer_id
                    ON repair_tickets(customer_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_tickets_device_id
                    ON repair_tickets(device_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_tickets_status
                    ON repair_tickets(repair_status);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_tickets_intake_date
                    ON repair_tickets(intake_date);

                CREATE TABLE IF NOT EXISTS repair_checkins (
                    checkin_id TEXT PRIMARY KEY,

                    repair_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,

                    technician TEXT NOT NULL DEFAULT '',

                    checkin_timestamp TEXT NOT NULL,

                    powers_on TEXT NOT NULL DEFAULT '',
                    battery_percentage INTEGER,
                    screen_condition TEXT NOT NULL DEFAULT '',
                    frame_condition TEXT NOT NULL DEFAULT '',
                    back_glass_condition TEXT NOT NULL DEFAULT '',
                    charging_port_condition TEXT NOT NULL DEFAULT '',
                    camera_condition TEXT NOT NULL DEFAULT '',
                    speaker_condition TEXT NOT NULL DEFAULT '',
                    microphone_condition TEXT NOT NULL DEFAULT '',
                    face_id_touch_id TEXT NOT NULL DEFAULT '',
                    liquid_damage TEXT NOT NULL DEFAULT '',
                    existing_damage TEXT NOT NULL DEFAULT '',
                    accessories_received TEXT NOT NULL DEFAULT '',
                    device_passcode TEXT NOT NULL DEFAULT '',
                    passcode_available TEXT NOT NULL DEFAULT '',
                    intake_notes TEXT NOT NULL DEFAULT '',

                  FOREIGN KEY (repair_id)
                      REFERENCES repair_tickets(ticket_id)
                      ON DELETE CASCADE,

                  FOREIGN KEY (customer_id)
                      REFERENCES customers(customer_id)
                      ON DELETE CASCADE,

                  FOREIGN KEY (device_id)
                      REFERENCES customer_devices(device_id)
                      ON DELETE CASCADE
              );

              CREATE INDEX IF NOT EXISTS
                      idx_repair_checkins_repair
                      ON repair_checkins(repair_id);

              CREATE INDEX IF NOT EXISTS
                      idx_repair_checkins_customer
                      ON repair_checkins(customer_id);

              CREATE INDEX IF NOT EXISTS
                      idx_repair_checkins_device
                      ON repair_checkins(device_id);

              CREATE TABLE IF NOT EXISTS wpforms_submissions (
                  submission_id TEXT PRIMARY KEY,

                  wpforms_form_id TEXT NOT NULL,
                  wpforms_entry_id TEXT NOT NULL,

                  customer_id TEXT NOT NULL,
                  device_id TEXT NOT NULL,
                  repair_id TEXT NOT NULL,
                  checkin_id TEXT NOT NULL,

                  received_at TEXT NOT NULL,

                  UNIQUE (
                      wpforms_form_id,
                      wpforms_entry_id
                  ),

                  FOREIGN KEY (customer_id)
                      REFERENCES customers(customer_id),

                  FOREIGN KEY (device_id)
                      REFERENCES customer_devices(device_id),

                  FOREIGN KEY (repair_id)
                      REFERENCES repair_tickets(ticket_id),

                  FOREIGN KEY (checkin_id)
                      REFERENCES repair_checkins(checkin_id)
              );

              CREATE INDEX IF NOT EXISTS
                  idx_wpforms_submissions_form_entry
                  ON wpforms_submissions(
                      wpforms_form_id,
                      wpforms_entry_id
                  );

              CREATE INDEX IF NOT EXISTS
                  idx_wpforms_submissions_repair
                  ON wpforms_submissions(repair_id);

                CREATE TABLE IF NOT EXISTS repair_events (
                    event_id TEXT PRIMARY KEY,
                    repair_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    old_value TEXT NOT NULL DEFAULT '',
                    new_value TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL DEFAULT 'Ryan Brown',

                    FOREIGN KEY(repair_id)
                        REFERENCES repair_tickets(ticket_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_events_repair_id
                    ON repair_events(repair_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_events_created_at
                    ON repair_events(created_at);
                """)

            self._migrate_customer_devices(connection)

            self._migrate_repair_tickets(connection)

    @staticmethod
    def _migrate_customer_devices(
        connection: sqlite3.Connection,
    ) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute("""
                PRAGMA table_info(
                    customer_devices
                )
                """).fetchall()
        }

        if "catalog_device_id" not in columns:
            connection.execute("""
                ALTER TABLE customer_devices
                ADD COLUMN catalog_device_id
                TEXT NOT NULL DEFAULT ''
                """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_customer_devices_catalog_device_id
                ON customer_devices(
                    catalog_device_id
                )
            """)

    @staticmethod
    def _migrate_repair_tickets(
        connection: sqlite3.Connection,
    ) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute("""
                PRAGMA table_info(
                    repair_tickets
                )
                """).fetchall()
        }

        if "priority" not in columns:
            connection.execute("""
                ALTER TABLE repair_tickets
                ADD COLUMN priority
                TEXT NOT NULL DEFAULT 'Normal'
                """)

        if "due_date" not in columns:
            connection.execute("""
                ALTER TABLE repair_tickets
                ADD COLUMN due_date
                TEXT NOT NULL DEFAULT ''
                """)

        if "technician" in columns:
            connection.execute("""
                UPDATE repair_tickets
                SET technician = 'Ryan Brown'
                WHERE technician IS NULL
                   OR TRIM(technician) = ''
                """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_repair_tickets_priority
                ON repair_tickets(priority)
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_repair_tickets_due_date
                ON repair_tickets(due_date)
            """)

    def next_id(
        self,
        *,
        table: str,
        column: str,
        prefix: str,
        width: int = 6,
    ) -> str:
        allowed_targets = {
            ("customers", "customer_id"),
            ("customer_devices", "device_id"),
            ("repair_tickets", "ticket_id"),
            ("repair_checkins", "checkin_id"),
            ("repair_events", "event_id"),
            ("wpforms_submissions", "submission_id"),
        }

        if (table, column) not in allowed_targets:
            raise ValueError(f"Unsupported ID target: {table}.{column}")

        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT {column}
                FROM {table}
                WHERE {column} LIKE ?
                """,
                (f"{prefix}%",),
            ).fetchall()

        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")

        highest = 0

        for row in rows:
            raw_value = row[column]

            if raw_value is None:
                continue

            match = pattern.fullmatch(str(raw_value))

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"{prefix}{highest + 1:0{width}d}"

    def create_customer(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
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
                    :customer_id,
                    :customer_type,
                    :first_name,
                    :last_name,
                    :business_name,
                    :email,
                    :mobile_phone,
                    :home_phone,
                    :work_phone,
                    :preferred_contact,
                    :billing_address,
                    :shipping_address,
                    :tax_exempt,
                    :active,
                    :date_created,
                    :last_modified,
                    :notes
                )
                """,
                record,
            )

        return record.copy()

    def list_customers(
        self,
        search: str = "",
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if search:
                value = f"%{search.strip()}%"

                rows = connection.execute(
                    """
                    SELECT *
                    FROM customers
                    WHERE first_name LIKE ?
                       OR last_name LIKE ?
                       OR business_name LIKE ?
                       OR email LIKE ?
                       OR mobile_phone LIKE ?
                       OR customer_id LIKE ?
                    ORDER BY customer_id
                    """,
                    (
                        value,
                        value,
                        value,
                        value,
                        value,
                        value,
                    ),
                ).fetchall()
            else:
                rows = connection.execute("""
                    SELECT *
                    FROM customers
                    ORDER BY customer_id
                    """).fetchall()

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

    def create_customer_device(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO customer_devices (
                    device_id,
                    customer_id,
                    catalog_device_id,
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
                    notes
                )
                VALUES (
                    :device_id,
                    :customer_id,
                    :catalog_device_id,
                    :manufacturer,
                    :device_family,
                    :device_model,
                    :serial_number,
                    :imei_service_tag,
                    :color,
                    :storage,
                    :carrier,
                    :purchase_date,
                    :warranty_expiration,
                    :active,
                    :notes
                )
                """,
                record,
            )

        return record.copy()

    def list_customer_devices(
        self,
        customer_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM customer_devices
                WHERE customer_id = ?
                  AND active = 1
                ORDER BY device_id
                """,
                (customer_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_customer_device(
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

    def create_repair(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
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
                    :ticket_id,
                    :customer_id,
                    :device_id,
                    :repair_status,
                    :intake_date,
                    :technician,
                    :priority,
                    :due_date,
                    :problem_description,
                    :diagnosis,
                    :estimated_cost,
                    :final_cost,
                    :date_completed,
                    :date_picked_up,
                    :warranty,
                    :notes,
                    :last_modified
                )
                """,
                record,
            )

        return record.copy()

    def list_repairs(
        self,
        search: str = "",
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if search:
                value = f"%{search.strip()}%"

                rows = connection.execute(
                    """
                    SELECT *
                    FROM repair_tickets
                    WHERE ticket_id LIKE ?
                       OR customer_id LIKE ?
                       OR device_id LIKE ?
                       OR repair_status LIKE ?
                       OR priority LIKE ?
                       OR problem_description LIKE ?
                    ORDER BY intake_date DESC,
                             ticket_id DESC
                    """,
                    (
                        value,
                        value,
                        value,
                        value,
                        value,
                        value,
                    ),
                ).fetchall()
            else:
                rows = connection.execute("""
                    SELECT *
                    FROM repair_tickets
                    ORDER BY intake_date DESC,
                             ticket_id DESC
                    """).fetchall()

        return [dict(row) for row in rows]

    def list_repair_queue(
        self,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT
                    r.ticket_id,
                    r.customer_id,
                    r.device_id,
                    r.repair_status,
                    r.intake_date,
                    r.problem_description,
                    r.estimated_cost,
                    r.final_cost,
                    r.technician,
                    r.priority,
                    r.due_date,
                    c.first_name,
                    c.last_name,
                    c.business_name,
                    d.manufacturer,
                    d.device_model,
                    d.catalog_device_id
                FROM repair_tickets AS r
                LEFT JOIN customers AS c
                    ON c.customer_id = r.customer_id
                LEFT JOIN customer_devices AS d
                    ON d.device_id = r.device_id
                ORDER BY
                    CASE r.priority
                        WHEN 'Urgent' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Normal' THEN 3
                        WHEN 'Low' THEN 4
                        ELSE 5
                    END,
                    CASE
                        WHEN r.due_date = '' THEN 1
                        ELSE 0
                    END,
                    r.due_date ASC,
                    r.intake_date DESC
                """).fetchall()

        return [dict(row) for row in rows]

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

    def update_repair(
        self,
        ticket_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_columns = {
            "repair_status",
            "notes",
            "final_cost",
            "technician",
            "priority",
            "due_date",
            "last_modified",
            "date_completed",
            "date_picked_up",
        }

        filtered_updates = {
            key: value for key, value in updates.items() if key in allowed_columns
        }

        if not filtered_updates:
            return self.get_repair(ticket_id)

        assignments = ", ".join(f"{column} = ?" for column in filtered_updates)

        parameters = list(filtered_updates.values())

        parameters.append(ticket_id)

        with self.connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE repair_tickets
                SET {assignments}
                WHERE ticket_id = ?
                """,
                parameters,
            )

            if cursor.rowcount == 0:
                return None

        return self.get_repair(ticket_id)

    def create_repair_checkin(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
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
                    :checkin_id,
                    :repair_id,
                    :customer_id,
                    :device_id,
                    :technician,
                    :checkin_timestamp,
                    :powers_on,
                    :battery_percentage,
                    :screen_condition,
                    :frame_condition,
                    :back_glass_condition,
                    :charging_port_condition,
                    :camera_condition,
                    :speaker_condition,
                    :microphone_condition,
                    :face_id_touch_id,
                    :liquid_damage,
                    :existing_damage,
                    :accessories_received,
                    :device_passcode,
                    :passcode_available,
                    :intake_notes
                )
                """,
                record,
            )

        return record.copy()

    def get_repair_checkin(
        self,
        repair_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_checkins
                WHERE repair_id = ?
                ORDER BY checkin_timestamp DESC,
                        checkin_id DESC
                LIMIT 1
                """,
                (repair_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_repair_checkin_by_id(
        self,
        checkin_id: str,
    ) -> dict[str, Any] | None:
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
            return None

        return dict(row)

    def update_repair_checkin(
        self,
        checkin_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_columns = {
            "technician",
            "powers_on",
            "battery_percentage",
            "screen_condition",
            "frame_condition",
            "back_glass_condition",
            "charging_port_condition",
            "camera_condition",
            "speaker_condition",
            "microphone_condition",
            "face_id_touch_id",
            "liquid_damage",
            "existing_damage",
            "accessories_received",
            "device_passcode",
            "passcode_available",
            "intake_notes",
        }

        filtered_updates = {
            key: value for key, value in updates.items() if key in allowed_columns
        }

        if not filtered_updates:
            return self.get_repair_checkin_by_id(checkin_id)

        assignments = ", ".join(f"{column} = ?" for column in filtered_updates)

        parameters = list(filtered_updates.values())

        parameters.append(checkin_id)

        with self.connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE repair_checkins
                SET {assignments}
                WHERE checkin_id = ?
                """,
                parameters,
            )

            if cursor.rowcount == 0:
                return None

        return self.get_repair_checkin_by_id(checkin_id)

    def create_repair_event(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        with self.connect() as connection:
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
                VALUES (
                    :event_id,
                    :repair_id,
                    :event_type,
                    :old_value,
                    :new_value,
                    :notes,
                    :created_at,
                    :created_by
                )
                """,
                record,
            )

        return record.copy()

    def list_repair_events(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_events
                WHERE repair_id = ?
                ORDER BY
                    created_at ASC,
                    event_id ASC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def counts(
        self,
    ) -> dict[str, Any]:
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

            status_rows = connection.execute("""
                SELECT
                    repair_status,
                    COUNT(*) AS total
                FROM repair_tickets
                GROUP BY repair_status
                ORDER BY repair_status
                """).fetchall()

        repairs_by_status = {
            str(row["repair_status"]): int(row["total"]) for row in status_rows
        }

        return {
            "customers": int(customers),
            "devices": int(devices),
            "repairs": int(repairs),
            "repairs_by_status": repairs_by_status,
        }

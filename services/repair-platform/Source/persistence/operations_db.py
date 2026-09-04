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

    def create_repair_pricing_item(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO repair_pricing_items (
                    repair_pricing_item_id,
                    repair_id,
                    pricing_record_id,
                    service_type_id,
                    variant_key,
                    service_type,
                    quality_class,
                    customer_facing_tier,
                    supplier,
                    supplier_product_id,
                    supplier_sku,
                    part_name,
                    quoted_unit_price_cents,
                    quantity,
                    line_total_cents,
                    pricing_snapshot_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    :repair_pricing_item_id,
                    :repair_id,
                    :pricing_record_id,
                    :service_type_id,
                    :variant_key,
                    :service_type,
                    :quality_class,
                    :customer_facing_tier,
                    :supplier,
                    :supplier_product_id,
                    :supplier_sku,
                    :part_name,
                    :quoted_unit_price_cents,
                    :quantity,
                    :line_total_cents,
                    :pricing_snapshot_at,
                    :created_at,
                    :updated_at
                )
                """,
                record,
            )

        return record.copy()

    def get_repair_pricing_item(
        self,
        repair_pricing_item_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_pricing_items
                WHERE repair_pricing_item_id = ?
                """,
                (repair_pricing_item_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_repair_pricing_items(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_pricing_items
                WHERE repair_id = ?
                ORDER BY
                    created_at,
                    repair_pricing_item_id
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def create_repair_authorization(
        self,
        record: dict[str, Any],
        repair_pricing_item_ids: list[str],
    ) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO repair_authorizations (
                    authorization_id,
                    repair_id,
                    authorization_type,
                    authorization_status,
                    quoted_total_cents,
                    currency,
                    terms_document_id,
                    terms_version,
                    customer_name,
                    authorization_method,
                    authorized_at,
                    declined_at,
                    created_at,
                    updated_at,
                    created_by
                )
                VALUES (
                    :authorization_id,
                    :repair_id,
                    :authorization_type,
                    :authorization_status,
                    :quoted_total_cents,
                    :currency,
                    :terms_document_id,
                    :terms_version,
                    :customer_name,
                    :authorization_method,
                    :authorized_at,
                    :declined_at,
                    :created_at,
                    :updated_at,
                    :created_by
                )
                """,
                record,
            )

            connection.executemany(
                """
                INSERT INTO repair_authorization_items (
                    authorization_id,
                    repair_pricing_item_id
                )
                VALUES (?, ?)
                """,
                [
                    (
                        record["authorization_id"],
                        repair_pricing_item_id,
                    )
                    for repair_pricing_item_id in repair_pricing_item_ids
                ],
            )

        return record.copy()

    def get_repair_authorization(
        self,
        authorization_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_authorizations
                WHERE authorization_id = ?
                """,
                (authorization_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_repair_authorizations(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_authorizations
                WHERE repair_id = ?
                ORDER BY
                    created_at,
                    authorization_id
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def list_repair_authorization_items(
        self,
        authorization_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    authorization_id,
                    repair_pricing_item_id
                FROM repair_authorization_items
                WHERE authorization_id = ?
                ORDER BY repair_pricing_item_id
                """,
                (authorization_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def delete_repair_pricing_item(
        self,
        repair_pricing_item_id: str,
    ) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM repair_pricing_items
                WHERE repair_pricing_item_id = ?
                """,
                (repair_pricing_item_id,),
            )

        return cursor.rowcount > 0

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


                CREATE TABLE IF NOT EXISTS service_pricing_catalog (
                    pricing_record_id TEXT PRIMARY KEY,

                    catalog_device_id TEXT NOT NULL,

                    service_type_id TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    service_category_id TEXT NOT NULL,

                    variant_key TEXT NOT NULL DEFAULT 'BASE',
                    variant_name TEXT,

                    supplier TEXT NOT NULL,
                    supplier_product_id TEXT NOT NULL,
                    supplier_sku TEXT NOT NULL,
                    part_name TEXT NOT NULL DEFAULT '',

                    quality_class TEXT,
                    quality_rank INTEGER,
                    customer_facing_tier TEXT,
                    commercial_selection_status TEXT,
                    recommended_action TEXT,

                    part_cost_cents INTEGER NOT NULL,

                    supplier_in_stock INTEGER,
                    supplier_stock_qty INTEGER,
                    supplier_observed_at TEXT,

                    default_labor_hours TEXT NOT NULL,
                    labor_profile_id TEXT NOT NULL,
                    labor_tier TEXT NOT NULL,
                    hourly_rate_cents INTEGER NOT NULL,
                    minimum_charge_cents INTEGER NOT NULL,

                    target_margin TEXT NOT NULL,
                    minimum_margin TEXT NOT NULL,

                    overhead_rate TEXT NOT NULL,
                    warranty_rate TEXT NOT NULL,
                    risk_rate TEXT NOT NULL,
                    processing_rate TEXT NOT NULL,

                    rounding_rule TEXT NOT NULL DEFAULT 'End in .99',

                    billable_labor_cost_cents INTEGER NOT NULL,
                    shipping_cents INTEGER NOT NULL,
                    consumables_cents INTEGER NOT NULL,

                    base_direct_cost_cents INTEGER NOT NULL,
                    total_internal_cost_cents INTEGER NOT NULL,

                    recommended_price_cents INTEGER NOT NULL,

                    gross_profit_cents INTEGER NOT NULL,
                    gross_margin TEXT NOT NULL,

                    pricing_status TEXT NOT NULL,

                    approved_price_cents INTEGER,
                    approval_status TEXT NOT NULL DEFAULT 'DRAFT',
                    approved_at TEXT,
                    approved_by TEXT,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    UNIQUE (
                        catalog_device_id,
                        service_type_id,
                        variant_key,
                        supplier,
                        supplier_product_id
                    )
                );

                CREATE INDEX IF NOT EXISTS
                    idx_service_pricing_catalog_device
                    ON service_pricing_catalog(
                        catalog_device_id
                    );

                CREATE INDEX IF NOT EXISTS
                    idx_service_pricing_catalog_service
                    ON service_pricing_catalog(
                        service_type_id,
                        variant_key
                    );

                CREATE INDEX IF NOT EXISTS
                    idx_service_pricing_catalog_supplier_product
                    ON service_pricing_catalog(
                        supplier,
                        supplier_product_id
                    );

                CREATE INDEX IF NOT EXISTS
                    idx_service_pricing_catalog_approval
                    ON service_pricing_catalog(
                        approval_status
                    );

                CREATE TABLE IF NOT EXISTS repair_pricing_items (
                    repair_pricing_item_id TEXT PRIMARY KEY,

                    repair_id TEXT NOT NULL,
                    pricing_record_id TEXT NOT NULL,

                    service_type_id TEXT NOT NULL,
                    variant_key TEXT NOT NULL DEFAULT 'BASE',

                    service_type TEXT NOT NULL,
                    quality_class TEXT,
                    customer_facing_tier TEXT,

                    supplier TEXT NOT NULL,
                    supplier_product_id TEXT NOT NULL,
                    supplier_sku TEXT NOT NULL,
                    part_name TEXT NOT NULL DEFAULT '',

                    quoted_unit_price_cents INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    line_total_cents INTEGER NOT NULL,

                    pricing_snapshot_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    FOREIGN KEY(repair_id)
                        REFERENCES repair_tickets(ticket_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,

                    FOREIGN KEY(pricing_record_id)
                        REFERENCES service_pricing_catalog(pricing_record_id)
                        ON UPDATE CASCADE
                        ON DELETE RESTRICT,

                    UNIQUE (
                        repair_id,
                        pricing_record_id
                    )
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_pricing_items_repair
                    ON repair_pricing_items(repair_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_pricing_items_pricing_record
                    ON repair_pricing_items(pricing_record_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_pricing_items_service
                    ON repair_pricing_items(
                        repair_id,
                        service_type_id
                    );

                CREATE TABLE IF NOT EXISTS repair_authorizations (
                    authorization_id TEXT PRIMARY KEY,

                    repair_id TEXT NOT NULL,

                    authorization_type TEXT NOT NULL
                        DEFAULT 'REPAIR_QUOTE',
                    authorization_status TEXT NOT NULL
                        DEFAULT 'PENDING',

                    quoted_total_cents INTEGER NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',

                    terms_document_id TEXT NOT NULL DEFAULT '',
                    terms_version TEXT NOT NULL DEFAULT '',

                    customer_name TEXT NOT NULL DEFAULT '',
                    authorization_method TEXT NOT NULL DEFAULT '',

                    authorized_at TEXT,
                    declined_at TEXT,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL DEFAULT 'Ryan Brown',

                    FOREIGN KEY(repair_id)
                        REFERENCES repair_tickets(ticket_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_authorizations_repair
                    ON repair_authorizations(repair_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_authorizations_status
                    ON repair_authorizations(
                        repair_id,
                        authorization_status
                    );

                CREATE TABLE IF NOT EXISTS repair_authorization_items (
                    authorization_id TEXT NOT NULL,
                    repair_pricing_item_id TEXT NOT NULL,

                    PRIMARY KEY (
                        authorization_id,
                        repair_pricing_item_id
                    ),

                    FOREIGN KEY(authorization_id)
                        REFERENCES repair_authorizations(
                            authorization_id
                        )
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,

                    FOREIGN KEY(repair_pricing_item_id)
                        REFERENCES repair_pricing_items(
                            repair_pricing_item_id
                        )
                        ON UPDATE CASCADE
                        ON DELETE RESTRICT
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_authorization_items_pricing_item
                    ON repair_authorization_items(
                        repair_pricing_item_id
                    );
                """)

            self._migrate_customer_devices(connection)
            self._migrate_repair_tickets(connection)
            self._migrate_service_pricing_catalog(connection)

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

    @staticmethod
    def _migrate_service_pricing_catalog(
        connection: sqlite3.Connection,
    ) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute("""
                PRAGMA table_info(service_pricing_catalog)
                """).fetchall()
        }

        additions = {
            "quality_class": "TEXT",
            "quality_rank": "INTEGER",
            "customer_facing_tier": "TEXT",
            "commercial_selection_status": "TEXT",
            "recommended_action": "TEXT",
        }

        for column_name, column_type in additions.items():
            if column_name in columns:
                continue

            connection.execute(f"""
                ALTER TABLE service_pricing_catalog
                ADD COLUMN {column_name} {column_type}
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
            ("service_pricing_catalog", "pricing_record_id"),
            ("repair_pricing_items", "repair_pricing_item_id"),
            ("repair_authorizations", "authorization_id"),
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

    def list_repair_payments(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_payments
                WHERE repair_id = ?
                ORDER BY
                    payment_timestamp DESC,
                    payment_id DESC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def repair_payment_summary(
        self,
        repair_id: str,
    ) -> dict[str, Any] | None:
        repair = self.get_repair(repair_id)

        if repair is None:
            return None

        final_cost_value = repair.get("final_cost")

        if final_cost_value is None:
            final_cost = 0.0
        else:
            try:
                final_cost = float(final_cost_value)
            except TypeError, ValueError:
                final_cost = 0.0

        final_cost = round(
            max(
                final_cost,
                0.0,
            ),
            2,
        )

        with self.connect() as connection:
            paid_row = connection.execute(
                """
                SELECT
                    COALESCE(
                        SUM(amount),
                        0
                    ) AS total_paid
                FROM repair_payments
                WHERE repair_id = ?
                  AND payment_status IN (
                      'Completed',
                      'Paid'
                  )
                """,
                (repair_id,),
            ).fetchone()

            refunded_row = connection.execute(
                """
                SELECT
                    COALESCE(
                        SUM(amount),
                        0
                    ) AS total_refunded
                FROM repair_payments
                WHERE repair_id = ?
                  AND payment_status IN (
                      'Refunded',
                      'Partially Refunded'
                  )
                """,
                (repair_id,),
            ).fetchone()

        total_paid = 0.0

        if paid_row is not None:
            total_paid = float(paid_row["total_paid"] or 0.0)

        total_refunded = 0.0

        if refunded_row is not None:
            total_refunded = float(refunded_row["total_refunded"] or 0.0)

        amount_paid = round(
            total_paid - total_refunded,
            2,
        )

        balance_due = round(
            max(
                final_cost - amount_paid,
                0.0,
            ),
            2,
        )

        if final_cost <= 0:
            payment_status = "No Balance"
        elif amount_paid <= 0:
            payment_status = "Unpaid"
        elif amount_paid < final_cost:
            payment_status = "Partially Paid"
        else:
            payment_status = "Paid"

        return {
            "repair_id": repair_id,
            "repair_status": str(
                repair.get(
                    "repair_status",
                    "",
                )
                or ""
            ),
            "final_cost": final_cost,
            "amount_paid": amount_paid,
            "balance_due": balance_due,
            "payment_status": payment_status,
            "currency": "USD",
        }

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

    def create_service_pricing_record(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        stored_record = record.copy()

        stored_record.setdefault("quality_class", None)
        stored_record.setdefault("quality_rank", None)
        stored_record.setdefault("customer_facing_tier", None)
        stored_record.setdefault("commercial_selection_status", None)
        stored_record.setdefault("recommended_action", None)

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO service_pricing_catalog (
                    pricing_record_id,
                    catalog_device_id,
                    service_type_id,
                    service_type,
                    service_category_id,
                    variant_key,
                    variant_name,
                    supplier,
                    supplier_product_id,
                    supplier_sku,
                    part_name,
                    quality_class,
                    quality_rank,
                    customer_facing_tier,
                    commercial_selection_status,
                    recommended_action,
                    part_cost_cents,
                    supplier_in_stock,
                    supplier_stock_qty,
                    supplier_observed_at,
                    default_labor_hours,
                    labor_profile_id,
                    labor_tier,
                    hourly_rate_cents,
                    minimum_charge_cents,
                    target_margin,
                    minimum_margin,
                    overhead_rate,
                    warranty_rate,
                    risk_rate,
                    processing_rate,
                    rounding_rule,
                    billable_labor_cost_cents,
                    shipping_cents,
                    consumables_cents,
                    base_direct_cost_cents,
                    total_internal_cost_cents,
                    recommended_price_cents,
                    gross_profit_cents,
                    gross_margin,
                    pricing_status,
                    approved_price_cents,
                    approval_status,
                    approved_at,
                    approved_by,
                    created_at,
                    updated_at
                )
                VALUES (
                    :pricing_record_id,
                    :catalog_device_id,
                    :service_type_id,
                    :service_type,
                    :service_category_id,
                    :variant_key,
                    :variant_name,
                    :supplier,
                    :supplier_product_id,
                    :supplier_sku,
                    :part_name,
                    :quality_class,
                    :quality_rank,
                    :customer_facing_tier,
                    :commercial_selection_status,
                    :recommended_action,
                    :part_cost_cents,
                    :supplier_in_stock,
                    :supplier_stock_qty,
                    :supplier_observed_at,
                    :default_labor_hours,
                    :labor_profile_id,
                    :labor_tier,
                    :hourly_rate_cents,
                    :minimum_charge_cents,
                    :target_margin,
                    :minimum_margin,
                    :overhead_rate,
                    :warranty_rate,
                    :risk_rate,
                    :processing_rate,
                    :rounding_rule,
                    :billable_labor_cost_cents,
                    :shipping_cents,
                    :consumables_cents,
                    :base_direct_cost_cents,
                    :total_internal_cost_cents,
                    :recommended_price_cents,
                    :gross_profit_cents,
                    :gross_margin,
                    :pricing_status,
                    :approved_price_cents,
                    :approval_status,
                    :approved_at,
                    :approved_by,
                    :created_at,
                    :updated_at
                )
                """,
                stored_record,
            )

        return stored_record

    def get_service_pricing_record(
        self,
        pricing_record_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM service_pricing_catalog
                WHERE pricing_record_id = ?
                """,
                (pricing_record_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_service_pricing_record_by_identity(
        self,
        *,
        catalog_device_id: str,
        service_type_id: str,
        variant_key: str,
        supplier: str,
        supplier_product_id: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM service_pricing_catalog
                WHERE catalog_device_id = ?
                  AND service_type_id = ?
                  AND variant_key = ?
                  AND supplier = ?
                  AND supplier_product_id = ?
                """,
                (
                    catalog_device_id,
                    service_type_id,
                    variant_key.strip().upper(),
                    supplier,
                    supplier_product_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_service_pricing_records(
        self,
        *,
        catalog_device_id: str | None = None,
        service_type_id: str | None = None,
        variant_key: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[Any] = []

        if catalog_device_id:
            conditions.append("catalog_device_id = ?")
            parameters.append(catalog_device_id)

        if service_type_id:
            conditions.append("service_type_id = ?")
            parameters.append(service_type_id)

        if variant_key:
            conditions.append("variant_key = ?")
            parameters.append(variant_key.strip().upper())

        if approval_status:
            conditions.append("approval_status = ?")
            parameters.append(approval_status.strip().upper())

        where_clause = ""

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM service_pricing_catalog
                {where_clause}
                ORDER BY
                    catalog_device_id,
                    service_type_id,
                    variant_key,
                    supplier,
                    supplier_product_id
                """,
                parameters,
            ).fetchall()

        return [dict(row) for row in rows]

    def update_service_pricing_record(
        self,
        pricing_record_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_columns = {
            "service_type",
            "service_category_id",
            "variant_name",
            "supplier_sku",
            "part_name",
            "quality_class",
            "quality_rank",
            "customer_facing_tier",
            "commercial_selection_status",
            "recommended_action",
            "part_cost_cents",
            "supplier_in_stock",
            "supplier_stock_qty",
            "supplier_observed_at",
            "default_labor_hours",
            "labor_profile_id",
            "labor_tier",
            "hourly_rate_cents",
            "minimum_charge_cents",
            "target_margin",
            "minimum_margin",
            "overhead_rate",
            "warranty_rate",
            "risk_rate",
            "processing_rate",
            "rounding_rule",
            "billable_labor_cost_cents",
            "shipping_cents",
            "consumables_cents",
            "base_direct_cost_cents",
            "total_internal_cost_cents",
            "recommended_price_cents",
            "gross_profit_cents",
            "gross_margin",
            "pricing_status",
            "updated_at",
        }

        filtered_updates = {
            key: value for key, value in updates.items() if key in allowed_columns
        }

        if not filtered_updates:
            return self.get_service_pricing_record(pricing_record_id)

        assignments = ", ".join(f"{column} = ?" for column in filtered_updates)

        parameters = list(filtered_updates.values())

        parameters.append(pricing_record_id)

        with self.connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE service_pricing_catalog
                SET {assignments}
                WHERE pricing_record_id = ?
                """,
                parameters,
            )

            if cursor.rowcount == 0:
                return None

        return self.get_service_pricing_record(pricing_record_id)

    def approve_service_pricing_record(
        self,
        pricing_record_id: str,
        *,
        approved_price_cents: int,
        approved_at: str,
        approved_by: str,
        updated_at: str,
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE service_pricing_catalog
                SET approved_price_cents = ?,
                    approval_status = 'APPROVED',
                    approved_at = ?,
                    approved_by = ?,
                    updated_at = ?
                WHERE pricing_record_id = ?
                  AND approval_status = 'DRAFT'
                """,
                (
                    approved_price_cents,
                    approved_at,
                    approved_by,
                    updated_at,
                    pricing_record_id,
                ),
            )

            if cursor.rowcount == 0:
                return None

        return self.get_service_pricing_record(pricing_record_id)

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

from __future__ import annotations

import re
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.database import OPERATIONS_DATABASE
from desktop.services.settings_service import SettingsService


class ProcurementError(RuntimeError):
    """Base error for Nocturnix procurement operations."""


class ProcurementNotFoundError(ProcurementError):
    """Raised when a procurement record cannot be found."""


class ProcurementValidationError(ProcurementError):
    """Raised when procurement input is invalid."""


class ProcurementStateError(ProcurementError):
    """Raised when a procurement state transition is not allowed."""


class ProcurementService:
    """
    Nocturnix repair procurement workflow.

    This service owns Nocturnix procurement state.

    Mobile Sentrix remains responsible for supplier-specific:

        product/entity IDs
        SKUs
        pricing
        availability
        stock quantity

    Nocturnix stores snapshots of supplier data when a procurement
    item is added.

    This service does NOT automatically place Mobile Sentrix orders.
    Supplier order placement remains human-approved/manual until a
    supported Mobile Sentrix order API is explicitly integrated.
    """

    STATUS_PENDING_APPROVAL = "Pending Approval"
    STATUS_APPROVED = "Approved"
    STATUS_READY_FOR_ORDER = "Ready for Order"
    STATUS_REJECTED = "Rejected"
    STATUS_ORDERED = "Ordered"
    STATUS_RECEIVED = "Received"
    STATUS_CANCELLED = "Cancelled"

    ACTIVE_STATUSES = {
        STATUS_PENDING_APPROVAL,
        STATUS_APPROVED,
        STATUS_READY_FOR_ORDER,
        STATUS_ORDERED,
    }

    FINAL_STATUSES = {
        STATUS_REJECTED,
        STATUS_RECEIVED,
        STATUS_CANCELLED,
    }

    def __init__(self) -> None:
        self.settings = SettingsService().load()

        self.database_path = self._resolve_database_path()
        self.backup_directory = self.database_path.parent / "backups"

        self.backup_limit = self.settings.backup_limit
        self.default_created_by = self.settings.default_created_by

        self.backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._ensure_schema()

    # =========================================================
    # Database
    # =========================================================

    def _resolve_database_path(self) -> Path:
        configured_path = self.settings.database_path.strip()

        if configured_path:
            return Path(configured_path).expanduser()

        return OPERATIONS_DATABASE

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("PRAGMA journal_mode = WAL")

        return connection

    def _ensure_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS repair_procurements (
                    procurement_id TEXT PRIMARY KEY,

                    repair_id TEXT NOT NULL,

                    supplier TEXT NOT NULL DEFAULT 'Mobile Sentrix',

                    procurement_status TEXT NOT NULL
                        DEFAULT 'Pending Approval',

                    requested_at TEXT NOT NULL,
                    requested_by TEXT NOT NULL DEFAULT '',

                    approved_at TEXT,
                    approved_by TEXT,

                    rejected_at TEXT,
                    rejected_by TEXT,
                    rejection_reason TEXT,

                    ready_for_order_at TEXT,

                    supplier_order_id TEXT,
                    supplier_order_date TEXT,

                    actual_supplier_cost REAL,

                    ordered_at TEXT,
                    ordered_by TEXT,

                    received_at TEXT,
                    received_by TEXT,

                    cancelled_at TEXT,
                    cancelled_by TEXT,
                    cancellation_reason TEXT,

                    notes TEXT NOT NULL DEFAULT '',

                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL DEFAULT '',

                    updated_at TEXT NOT NULL,

                    FOREIGN KEY (repair_id)
                        REFERENCES repair_tickets(ticket_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurements_repair_id
                ON repair_procurements(repair_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurements_status
                ON repair_procurements(procurement_status);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurements_supplier_order_id
                ON repair_procurements(supplier_order_id);


                CREATE TABLE IF NOT EXISTS repair_procurement_items (
                    procurement_item_id TEXT PRIMARY KEY,

                    procurement_id TEXT NOT NULL,
                    repair_id TEXT NOT NULL,

                    supplier TEXT NOT NULL DEFAULT 'Mobile Sentrix',

                    supplier_product_id TEXT,
                    supplier_sku TEXT,

                    product_name TEXT NOT NULL DEFAULT '',
                    product_url TEXT,

                    quantity INTEGER NOT NULL DEFAULT 1,

                    unit_cost REAL,
                    estimated_line_total REAL,

                    supplier_in_stock INTEGER,
                    supplier_stock_quantity INTEGER,

                    supplier_observed_at TEXT,

                    received_quantity INTEGER NOT NULL DEFAULT 0,

                    notes TEXT NOT NULL DEFAULT '',

                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL DEFAULT '',

                    updated_at TEXT NOT NULL,

                    FOREIGN KEY (procurement_id)
                        REFERENCES repair_procurements(procurement_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,

                    FOREIGN KEY (repair_id)
                        REFERENCES repair_tickets(ticket_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurement_items_procurement_id
                ON repair_procurement_items(procurement_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurement_items_repair_id
                ON repair_procurement_items(repair_id);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurement_items_supplier_sku
                ON repair_procurement_items(supplier_sku);

                CREATE INDEX IF NOT EXISTS
                    idx_repair_procurement_items_supplier_product_id
                ON repair_procurement_items(supplier_product_id);
                """)

            connection.commit()

    # =========================================================
    # Backup
    # =========================================================

    def create_write_backup(self) -> Path | None:
        """
        Create a safety copy of the operations database before writes.

        This follows the existing Nocturnix payment-service practice
        of protecting the SQLite operations database before mutation.
        """

        if not self.database_path.exists():
            return None

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        backup_path = self.backup_directory / (
            f"{self.database_path.stem}"
            f".before-procurement-write-{timestamp}"
            f"{self.database_path.suffix}"
        )

        shutil.copy2(
            self.database_path,
            backup_path,
        )

        self._prune_backups()

        return backup_path

    def _prune_backups(self) -> None:
        if self.backup_limit <= 0:
            return

        backups = sorted(
            self.backup_directory.glob(
                (
                    f"{self.database_path.stem}"
                    ".before-procurement-write-*"
                    f"{self.database_path.suffix}"
                )
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        for backup in backups[self.backup_limit :]:
            try:
                backup.unlink()
            except OSError:
                continue

    # =========================================================
    # Validation helpers
    # =========================================================

    @staticmethod
    def _required_text(
        value: object,
        label: str,
    ) -> str:
        text = str(value if value is not None else "").strip()

        if not text:
            raise ProcurementValidationError(f"{label} is required.")

        return text

    @staticmethod
    def _optional_text(
        value: object,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _optional_money(
        value: object,
        label: str,
    ) -> float | None:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        try:
            number = float(text)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProcurementValidationError(f"{label} must be numeric.") from exc

        if number < 0:
            raise ProcurementValidationError(f"{label} cannot be negative.")

        return round(
            number,
            2,
        )

    @staticmethod
    def _required_quantity(
        value: object,
    ) -> int:
        try:
            quantity = int(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProcurementValidationError(
                "Quantity must be a whole number."
            ) from exc

        if quantity < 1:
            raise ProcurementValidationError("Quantity must be at least 1.")

        return quantity

    @staticmethod
    def _optional_integer(
        value: object,
        *,
        minimum: int | None = None,
    ) -> int | None:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        try:
            number = int(text)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProcurementValidationError("Expected a whole-number value.") from exc

        if minimum is not None and number < minimum:
            raise ProcurementValidationError(
                ("Value cannot be less than " f"{minimum}.")
            )

        return number

    @staticmethod
    def _optional_boolean_integer(
        value: object,
    ) -> int | None:
        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return 1 if value else 0

        normalized = str(value).strip().lower()

        if normalized in {
            "1",
            "true",
            "yes",
            "in stock",
        }:
            return 1

        if normalized in {
            "0",
            "false",
            "no",
            "out of stock",
        }:
            return 0

        raise ProcurementValidationError("Supplier stock status is invalid.")

    # =========================================================
    # Repair validation
    # =========================================================

    def _require_repair(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_tickets
                WHERE ticket_id = ?
                """,
                (repair_id,),
            ).fetchone()

        if row is None:
            raise ProcurementNotFoundError("Repair ticket not found.")

        return dict(row)

    # =========================================================
    # ID generation
    # =========================================================

    @staticmethod
    def _next_prefixed_id(
        connection: sqlite3.Connection,
        *,
        table: str,
        column: str,
        prefix: str,
    ) -> str:
        rows = connection.execute(f"""
            SELECT {column}
            FROM {table}
            """).fetchall()

        highest = 0

        pattern = re.compile(rf"{re.escape(prefix)}(\d{{6}})")

        for row in rows:
            current_id = str(row[column] or "")

            match = pattern.fullmatch(current_id)

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"{prefix}" f"{highest + 1:06d}"

    # =========================================================
    # Procurement creation
    # =========================================================

    def create_procurement(
        self,
        repair_id: str,
        values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        values = dict(values) if values is not None else {}

        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        self._require_repair(repair_id)

        supplier = self._optional_text(values.get("supplier")) or "Mobile Sentrix"

        requested_by = (
            self._optional_text(values.get("requested_by")) or self.default_created_by
        )

        created_by = self._optional_text(values.get("created_by")) or requested_by

        notes = self._optional_text(values.get("notes"))

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            procurement_id = self._next_prefixed_id(
                connection,
                table=("repair_procurements"),
                column=("procurement_id"),
                prefix="PROC",
            )

            connection.execute(
                """
                INSERT INTO repair_procurements (
                    procurement_id,
                    repair_id,
                    supplier,
                    procurement_status,
                    requested_at,
                    requested_by,
                    notes,
                    created_at,
                    created_by,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    procurement_id,
                    repair_id,
                    supplier,
                    self.STATUS_PENDING_APPROVAL,
                    now,
                    requested_by,
                    notes,
                    now,
                    created_by,
                    now,
                ),
            )

            connection.commit()

        procurement = self.get_procurement(procurement_id)

        if procurement is None:
            raise RuntimeError(
                ("Procurement was created but " "could not be reloaded.")
            )

        return procurement

    # =========================================================
    # Item creation
    # =========================================================

    def add_item(
        self,
        procurement_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        procurement = self.require_procurement(procurement_id)

        if procurement["procurement_status"] != self.STATUS_PENDING_APPROVAL:
            raise ProcurementStateError(
                (
                    "Procurement items may only be "
                    "changed while the procurement "
                    "is Pending Approval."
                )
            )

        quantity = self._required_quantity(
            values.get(
                "quantity",
                1,
            )
        )

        unit_cost = self._optional_money(
            values.get("unit_cost"),
            "Unit cost",
        )

        estimated_line_total = (
            round(
                unit_cost * quantity,
                2,
            )
            if unit_cost is not None
            else None
        )

        supplier = self._optional_text(values.get("supplier")) or str(
            procurement["supplier"]
        )

        supplier_product_id = self._optional_text(values.get("supplier_product_id"))

        supplier_sku = self._optional_text(values.get("supplier_sku"))

        product_name = self._optional_text(values.get("product_name"))

        if not supplier_product_id and not supplier_sku and not product_name:
            raise ProcurementValidationError(
                (
                    "A procurement item must include "
                    "a supplier product ID, supplier "
                    "SKU, or product name."
                )
            )

        supplier_in_stock = self._optional_boolean_integer(
            values.get("supplier_in_stock")
        )

        supplier_stock_quantity = self._optional_integer(
            values.get("supplier_stock_quantity"),
            minimum=0,
        )

        supplier_observed_at = (
            self._optional_text(values.get("supplier_observed_at"))
            or datetime.now(UTC).isoformat()
        )

        product_url = self._optional_text(values.get("product_url"))

        notes = self._optional_text(values.get("notes"))

        created_by = (
            self._optional_text(values.get("created_by")) or self.default_created_by
        )

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            procurement_item_id = self._next_prefixed_id(
                connection,
                table=("repair_procurement_items"),
                column=("procurement_item_id"),
                prefix="PRI",
            )

            connection.execute(
                """
                INSERT INTO repair_procurement_items (
                    procurement_item_id,
                    procurement_id,
                    repair_id,
                    supplier,
                    supplier_product_id,
                    supplier_sku,
                    product_name,
                    product_url,
                    quantity,
                    unit_cost,
                    estimated_line_total,
                    supplier_in_stock,
                    supplier_stock_quantity,
                    supplier_observed_at,
                    received_quantity,
                    notes,
                    created_at,
                    created_by,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?
                )
                """,
                (
                    procurement_item_id,
                    procurement["procurement_id"],
                    procurement["repair_id"],
                    supplier,
                    supplier_product_id or None,
                    supplier_sku or None,
                    product_name,
                    product_url or None,
                    quantity,
                    unit_cost,
                    estimated_line_total,
                    supplier_in_stock,
                    supplier_stock_quantity,
                    supplier_observed_at,
                    0,
                    notes,
                    now,
                    created_by,
                    now,
                ),
            )

            connection.commit()

        item = self.get_item(procurement_item_id)

        if item is None:
            raise RuntimeError(
                ("Procurement item was created " "but could not be reloaded.")
            )

        return item

    # =========================================================
    # Lookups
    # =========================================================

    def get_procurement(
        self,
        procurement_id: str,
    ) -> dict[str, Any] | None:
        procurement_id = str(procurement_id).strip()

        if not procurement_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_procurements
                WHERE procurement_id = ?
                """,
                (procurement_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def require_procurement(
        self,
        procurement_id: str,
    ) -> dict[str, Any]:
        procurement = self.get_procurement(procurement_id)

        if procurement is None:
            raise ProcurementNotFoundError("Procurement request not found.")

        return procurement

    def list_repair_procurements(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        self._require_repair(repair_id)

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_procurements
                WHERE repair_id = ?
                ORDER BY
                    created_at DESC,
                    procurement_id DESC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_item(
        self,
        procurement_item_id: str,
    ) -> dict[str, Any] | None:
        procurement_item_id = str(procurement_item_id).strip()

        if not procurement_item_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_procurement_items
                WHERE procurement_item_id = ?
                """,
                (procurement_item_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_items(
        self,
        procurement_id: str,
    ) -> list[dict[str, Any]]:
        self.require_procurement(procurement_id)

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_procurement_items
                WHERE procurement_id = ?
                ORDER BY
                    created_at ASC,
                    procurement_item_id ASC
                """,
                (procurement_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    # =========================================================
    # Status helpers
    # =========================================================

    def _set_status(
        self,
        procurement_id: str,
        *,
        expected_statuses: set[str],
        new_status: str,
        updates: dict[str, object | None],
    ) -> dict[str, Any]:
        procurement = self.require_procurement(procurement_id)

        current_status = str(procurement["procurement_status"])

        if current_status not in expected_statuses:
            raise ProcurementStateError(
                (
                    "Cannot change procurement "
                    f"{procurement_id} from "
                    f"{current_status!r} to "
                    f"{new_status!r}."
                )
            )

        now = datetime.now(UTC).isoformat()

        assignments = [
            "procurement_status = ?",
            "updated_at = ?",
        ]

        parameters: list[object | None] = [
            new_status,
            now,
        ]

        for column, value in updates.items():
            assignments.append(f"{column} = ?")

            parameters.append(value)

        parameters.append(procurement_id)

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                f"""
                UPDATE repair_procurements
                SET {", ".join(assignments)}
                WHERE procurement_id = ?
                """,
                parameters,
            )

            connection.commit()

        updated = self.get_procurement(procurement_id)

        if updated is None:
            raise RuntimeError(
                ("Procurement was updated but " "could not be reloaded.")
            )

        return updated

    # =========================================================
    # Approval workflow
    # =========================================================

    def approve(
        self,
        procurement_id: str,
        *,
        approved_by: str = "",
    ) -> dict[str, Any]:
        if not self.list_items(procurement_id):
            raise ProcurementValidationError(
                (
                    "A procurement request cannot "
                    "be approved without at least "
                    "one item."
                )
            )

        actor = approved_by.strip() or self.default_created_by

        now = datetime.now(UTC).isoformat()

        return self._set_status(
            procurement_id,
            expected_statuses={
                self.STATUS_PENDING_APPROVAL,
            },
            new_status=(self.STATUS_APPROVED),
            updates={
                "approved_at": now,
                "approved_by": actor,
            },
        )

    def mark_ready_for_order(
        self,
        procurement_id: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()

        return self._set_status(
            procurement_id,
            expected_statuses={
                self.STATUS_APPROVED,
            },
            new_status=(self.STATUS_READY_FOR_ORDER),
            updates={
                "ready_for_order_at": now,
            },
        )

    def reject(
        self,
        procurement_id: str,
        *,
        rejected_by: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        actor = rejected_by.strip() or self.default_created_by

        now = datetime.now(UTC).isoformat()

        return self._set_status(
            procurement_id,
            expected_statuses={
                self.STATUS_PENDING_APPROVAL,
            },
            new_status=(self.STATUS_REJECTED),
            updates={
                "rejected_at": now,
                "rejected_by": actor,
                "rejection_reason": (reason.strip() or None),
            },
        )

    # =========================================================
    # Manual supplier order
    # =========================================================

    def record_manual_order(
        self,
        procurement_id: str,
        *,
        supplier_order_id: str,
        actual_supplier_cost: object = None,
        ordered_by: str = "",
        supplier_order_date: str = "",
    ) -> dict[str, Any]:
        supplier_order_id = self._required_text(
            supplier_order_id,
            "Supplier order ID",
        )

        cost = self._optional_money(
            actual_supplier_cost,
            "Actual supplier cost",
        )

        actor = ordered_by.strip() or self.default_created_by

        now = datetime.now(UTC).isoformat()

        order_date = supplier_order_date.strip() or now

        return self._set_status(
            procurement_id,
            expected_statuses={
                self.STATUS_READY_FOR_ORDER,
            },
            new_status=(self.STATUS_ORDERED),
            updates={
                "supplier_order_id": (supplier_order_id),
                "supplier_order_date": (order_date),
                "actual_supplier_cost": (cost),
                "ordered_at": now,
                "ordered_by": actor,
            },
        )

    # =========================================================
    # Receiving
    # =========================================================

    def receive(
        self,
        procurement_id: str,
        *,
        received_by: str = "",
    ) -> dict[str, Any]:
        procurement = self.require_procurement(procurement_id)

        if procurement["procurement_status"] != self.STATUS_ORDERED:
            raise ProcurementStateError(
                ("Only an Ordered procurement " "can be marked Received.")
            )

        items = self.list_items(procurement_id)

        actor = received_by.strip() or self.default_created_by

        now = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            for item in items:
                connection.execute(
                    """
                    UPDATE repair_procurement_items
                    SET
                        received_quantity = quantity,
                        updated_at = ?
                    WHERE procurement_item_id = ?
                    """,
                    (
                        now,
                        item["procurement_item_id"],
                    ),
                )

            connection.execute(
                """
                UPDATE repair_procurements
                SET
                    procurement_status = ?,
                    received_at = ?,
                    received_by = ?,
                    updated_at = ?
                WHERE procurement_id = ?
                """,
                (
                    self.STATUS_RECEIVED,
                    now,
                    actor,
                    now,
                    procurement_id,
                ),
            )

            connection.commit()

        updated = self.get_procurement(procurement_id)

        if updated is None:
            raise RuntimeError(
                ("Procurement was received but " "could not be reloaded.")
            )

        return updated

    # =========================================================
    # Cancellation
    # =========================================================

    def cancel(
        self,
        procurement_id: str,
        *,
        cancelled_by: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        actor = cancelled_by.strip() or self.default_created_by

        now = datetime.now(UTC).isoformat()

        return self._set_status(
            procurement_id,
            expected_statuses={
                self.STATUS_PENDING_APPROVAL,
                self.STATUS_APPROVED,
                self.STATUS_READY_FOR_ORDER,
            },
            new_status=(self.STATUS_CANCELLED),
            updates={
                "cancelled_at": now,
                "cancelled_by": actor,
                "cancellation_reason": (reason.strip() or None),
            },
        )

    # =========================================================
    # Totals
    # =========================================================

    def procurement_summary(
        self,
        procurement_id: str,
    ) -> dict[str, Any]:
        procurement = self.require_procurement(procurement_id)

        items = self.list_items(procurement_id)

        estimated_total = round(
            sum(float(item["estimated_line_total"] or 0.0) for item in items),
            2,
        )

        requested_units = sum(int(item["quantity"] or 0) for item in items)

        received_units = sum(int(item["received_quantity"] or 0) for item in items)

        return {
            "procurement_id": (procurement["procurement_id"]),
            "repair_id": (procurement["repair_id"]),
            "supplier": (procurement["supplier"]),
            "procurement_status": (procurement["procurement_status"]),
            "item_count": len(items),
            "requested_units": (requested_units),
            "received_units": (received_units),
            "estimated_total": (estimated_total),
            "actual_supplier_cost": (procurement.get("actual_supplier_cost")),
            "supplier_order_id": (procurement.get("supplier_order_id")),
        }

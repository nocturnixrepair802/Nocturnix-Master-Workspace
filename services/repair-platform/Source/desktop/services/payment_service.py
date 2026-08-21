from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.database import OPERATIONS_DATABASE
from desktop.services.settings_service import SettingsService


class PaymentService:
    def __init__(self) -> None:
        self.settings = SettingsService().load()

        self.database_path = self._resolve_database_path()
        self.backup_directory = self.database_path.parent / "backups"
        self.backup_limit = self.settings.backup_limit

        self.default_currency = self.settings.default_currency
        self.default_created_by = self.settings.default_created_by

        self.backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._ensure_schema()

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------


    def _resolve_database_path(
        self,
    ) -> Path:
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
            connection.execute("""
                CREATE TABLE IF NOT EXISTS repair_payments (
                    payment_id TEXT PRIMARY KEY,
                    repair_id TEXT NOT NULL,
                    payment_status TEXT NOT NULL DEFAULT 'Completed',
                    payment_method TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    payment_timestamp TEXT NOT NULL,
                    reference_number TEXT,
                    square_payment_id TEXT,
                    square_order_id TEXT,
                    square_terminal_checkout_id TEXT,
                    square_receipt_url TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL DEFAULT 'Ryan Brown',
                    FOREIGN KEY (repair_id)
                        REFERENCES repair_tickets(ticket_id)
                )
                """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_repair_payments_repair_id
                ON repair_payments(repair_id)
                """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_repair_payments_square_payment_id
                ON repair_payments(square_payment_id)
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS payment_operations (
                    operation_id TEXT PRIMARY KEY,
                    repair_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    operation_status TEXT NOT NULL,
                    amount REAL NOT NULL,
                    square_terminal_checkout_id TEXT,
                    square_payment_id TEXT,
                    square_refund_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    notes TEXT,
                    FOREIGN KEY (repair_id)
                        REFERENCES repair_tickets(ticket_id)
                )
                """)
        payment_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(repair_payments)"
            ).fetchall()
        }

        if "square_refund_id" not in payment_columns:
            connection.execute("""
                ALTER TABLE repair_payments
                ADD COLUMN square_refund_id TEXT
                """)

        if "refunded_square_payment_id" not in payment_columns:
            connection.execute("""
                ALTER TABLE repair_payments
                ADD COLUMN refunded_square_payment_id TEXT
                """)

        connection.execute("""
            UPDATE repair_payments
            SET
                square_refund_id = reference_number
            WHERE payment_method = 'Square Refund'
              AND square_refund_id IS NULL
              AND reference_number IS NOT NULL
              AND TRIM(reference_number) <> ''
              AND reference_number IN (
                  SELECT reference_number
                  FROM repair_payments
                  WHERE payment_method = 'Square Refund'
                    AND reference_number IS NOT NULL
                    AND TRIM(reference_number) <> ''
                  GROUP BY reference_number
                  HAVING COUNT(*) = 1
              )
            """)

        refund_rows = connection.execute("""
            SELECT
                payment_id,
                notes
            FROM repair_payments
            WHERE payment_method = 'Square Refund'
              AND refunded_square_payment_id IS NULL
              AND notes IS NOT NULL
            """).fetchall()

        refund_note_pattern = re.compile(r"^Square refund for (.+)\.$")

        for row in refund_rows:
            notes = str(row["notes"] or "").strip()
            match = refund_note_pattern.fullmatch(notes)

            if match is None:
                continue

            refunded_square_payment_id = match.group(1).strip()

            if not refunded_square_payment_id:
                continue

            connection.execute(
                """
                UPDATE repair_payments
                SET refunded_square_payment_id = ?
                WHERE payment_id = ?
                """,
                (
                    refunded_square_payment_id,
                    row["payment_id"],
                ),
            )

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_repair_payments_square_refund_id
            ON repair_payments(square_refund_id)
            WHERE square_refund_id IS NOT NULL
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_repair_payments_refunded_square_payment_id
            ON repair_payments(refunded_square_payment_id)
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_payment_operations_repair_id
            ON payment_operations(repair_id)
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_payment_operations_status
            ON payment_operations(operation_status)
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_payment_operations_terminal_checkout
            ON payment_operations(square_terminal_checkout_id)
            """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_payment_operations_refund_id
            ON payment_operations(square_refund_id)
            """)

        connection.commit()
    # ---------------------------------------------------------
    # BACKUPS
    # ---------------------------------------------------------

    def create_write_backup(self) -> Path | None:
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

    def _prune_backups(self) -> None:
        backups = sorted(
            self.backup_directory.glob("nocturnix_operations-*.sqlite3"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[self.backup_limit :]:
            old_backup.unlink(missing_ok=True)

    # ---------------------------------------------------------
    # VALUE HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _required_text(
        value: object,
        field_name: str,
    ) -> str:
        text = str(value or "").strip()

        if not text:
            raise ValueError(f"{field_name} is required.")

        return text

    @staticmethod
    def _optional_text(
        value: object,
    ) -> str:
        return str(value or "").strip()

    @staticmethod
    def _required_amount(
        value: object,
    ) -> float:
        if value is None:
            raise ValueError("Payment amount is required.")

        text = str(value).strip()

        if not text:
            raise ValueError("Payment amount is required.")

        try:
            amount = float(text)
        except ValueError as exc:
            raise ValueError("Payment amount must be a valid number.") from exc

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        return round(
            amount,
            2,
        )

    # ---------------------------------------------------------
    # REPAIR LOOKUP
    # ---------------------------------------------------------

    def get_repair(
        self,
        repair_id: str,
    ) -> dict[str, Any] | None:
        repair_id = str(repair_id).strip()

        if not repair_id:
            return None

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
            return None

        return dict(row)

    def _require_repair(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        repair = self.get_repair(repair_id)

        if repair is None:
            raise ValueError(f"Repair not found: {repair_id}")

        return repair

    def get_payment_by_reference_number(
        self,
        reference_number: str,
    ) -> dict[str, Any] | None:
        reference_number = str(reference_number).strip()

        if not reference_number:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_payments
                WHERE reference_number = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (reference_number,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    # ---------------------------------------------------------
    # PAYMENT IDS
    # ---------------------------------------------------------

    def _next_payment_id(
        self,
        connection: sqlite3.Connection,
    ) -> str:
        rows = connection.execute("""
            SELECT payment_id
            FROM repair_payments
            """).fetchall()

        highest = 0

        for row in rows:
            payment_id = str(row["payment_id"] or "")

            match = re.fullmatch(
                r"PAY(\d{6})",
                payment_id,
            )

            if match is None:
                continue

            number = int(match.group(1))

            highest = max(
                highest,
                number,
            )

        return f"PAY{highest + 1:06d}"

    # ---------------------------------------------------------
    # CREATE PAYMENT
    # ---------------------------------------------------------

    def create_payment(
        self,
        repair_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        self._require_repair(repair_id)

        payment_method = self._required_text(
            values.get("payment_method"),
            "Payment method",
        )

        amount = self._required_amount(values.get("amount"))

        payment_status = (
            self._optional_text(values.get("payment_status")) or "Completed"
        )

        currency = (
            self._optional_text(values.get("currency")) or self.default_currency
        ).upper()

        payment_timestamp = (
            self._optional_text(values.get("payment_timestamp"))
            or datetime.now(UTC).isoformat()
        )

        reference_number = self._optional_text(values.get("reference_number"))

        square_payment_id = self._optional_text(values.get("square_payment_id"))

        square_order_id = self._optional_text(values.get("square_order_id"))

        square_terminal_checkout_id = self._optional_text(
            values.get("square_terminal_checkout_id")
        )

        square_receipt_url = self._optional_text(values.get("square_receipt_url"))

        notes = self._optional_text(values.get("notes"))

        square_refund_id = self._optional_text(values.get("square_refund_id"))

        refunded_square_payment_id = self._optional_text(
            values.get("refunded_square_payment_id")
        )

        created_by = (
            self._optional_text(values.get("created_by")) or self.default_created_by
        )

        created_at = datetime.now(UTC).isoformat()

        self.create_write_backup()

        with self.connect() as connection:
            payment_id = self._next_payment_id(connection)

            connection.execute(
                """
                INSERT INTO repair_payments (
                    payment_id,
                    repair_id,
                    payment_status,
                    payment_method,
                    amount,
                    currency,
                    payment_timestamp,
                    reference_number,
                    square_payment_id,
                    square_order_id,
                    square_terminal_checkout_id,
                    square_receipt_url,
                    square_refund_id,
                    refunded_square_payment_id,
                    notes,
                    created_at,
                    created_by
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    payment_id,
                    repair_id,
                    payment_status,
                    payment_method,
                    amount,
                    currency,
                    payment_timestamp,
                    reference_number or None,
                    square_payment_id or None,
                    square_order_id or None,
                    square_terminal_checkout_id or None,
                    square_receipt_url or None,
                    square_refund_id or None,
                    refunded_square_payment_id or None,
                    notes or None,
                    created_at,
                    created_by,
                ),
            )

            connection.commit()

        payment = self.get_payment(payment_id)

        if payment is None:
            raise RuntimeError(
                "Payment was created but could not be reloaded."
            )

        return payment
    # ---------------------------------------------------------
    # PAYMENT LOOKUPS
    # ---------------------------------------------------------

    def get_payment(
        self,
        payment_id: str,
    ) -> dict[str, Any] | None:
        payment_id = str(payment_id).strip()

        if not payment_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_payments
                WHERE payment_id = ?
                """,
                (payment_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_payment_by_square_id(
        self,
        square_payment_id: str,
    ) -> dict[str, Any] | None:
        square_payment_id = str(square_payment_id).strip()

        if not square_payment_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_payments
                WHERE square_payment_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (square_payment_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_repair_payments(
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
                FROM repair_payments
                WHERE repair_id = ?
                ORDER BY
                    payment_timestamp DESC,
                    payment_id DESC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def create_payment_operation(
        self,
        repair_id: str,
        *,
        operation_type: str,
        operation_status: str,
        amount: float,
        square_terminal_checkout_id: str = "",
        square_payment_id: str = "",
        square_refund_id: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        self._require_repair(repair_id)

        operation_type = self._required_text(
            operation_type,
            "Operation type",
        )

        operation_status = self._required_text(
            operation_status,
            "Operation status",
        )

        amount = self._required_amount(amount)

        timestamp = datetime.now(UTC).isoformat()

        with self.connect() as connection:
            rows = connection.execute("""
                SELECT operation_id
                FROM payment_operations
                """).fetchall()

            highest = 0

            for row in rows:
                operation_id = str(row["operation_id"] or "")

                match = re.fullmatch(
                    r"POP(\d{6})",
                    operation_id,
                )

                if match is None:
                    continue

                highest = max(
                    highest,
                    int(match.group(1)),
                )

            operation_id = f"POP{highest + 1:06d}"

            connection.execute(
                """
                INSERT INTO payment_operations (
                    operation_id,
                    repair_id,
                    operation_type,
                    operation_status,
                    amount,
                    square_terminal_checkout_id,
                    square_payment_id,
                    square_refund_id,
                    created_at,
                    updated_at,
                    completed_at,
                    notes
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    operation_id,
                    repair_id,
                    operation_type,
                    operation_status,
                    amount,
                    square_terminal_checkout_id or None,
                    square_payment_id or None,
                    square_refund_id or None,
                    timestamp,
                    timestamp,
                    None,
                    notes or None,
                ),
            )

            connection.commit()

        operation = self.get_payment_operation(operation_id)

        if operation is None:
            raise RuntimeError(
                "Payment operation was created " "but could not be reloaded."
            )

        return operation

    def get_payment_operation(
        self,
        operation_id: str,
    ) -> dict[str, Any] | None:
        operation_id = str(operation_id).strip()

        if not operation_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM payment_operations
                WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def update_payment_operation(
        self,
        operation_id: str,
        *,
        operation_status: str | None = None,
        square_payment_id: str | None = None,
        square_refund_id: str | None = None,
        completed: bool = False,
        notes: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_payment_operation(operation_id)

        if current is None:
            raise ValueError(f"Payment operation not found: " f"{operation_id}")

        status = (
            operation_status
            if operation_status is not None
            else str(current["operation_status"])
        )

        payment_id = (
            square_payment_id
            if square_payment_id is not None
            else str(
                current.get(
                    "square_payment_id",
                    "",
                )
                or ""
            )
        )

        refund_id = (
            square_refund_id
            if square_refund_id is not None
            else str(
                current.get(
                    "square_refund_id",
                    "",
                )
                or ""
            )
        )

        new_notes = (
            notes
            if notes is not None
            else str(
                current.get(
                    "notes",
                    "",
                )
                or ""
            )
        )

        updated_at = datetime.now(UTC).isoformat()

        completed_at = updated_at if completed else current.get("completed_at")

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE payment_operations
                SET
                    operation_status = ?,
                    square_payment_id = ?,
                    square_refund_id = ?,
                    updated_at = ?,
                    completed_at = ?,
                    notes = ?
                WHERE operation_id = ?
                """,
                (
                    status,
                    payment_id or None,
                    refund_id or None,
                    updated_at,
                    completed_at,
                    new_notes or None,
                    operation_id,
                ),
            )

            connection.commit()

        updated = self.get_payment_operation(operation_id)

        if updated is None:
            raise RuntimeError(
                "Payment operation was updated " "but could not be reloaded."
            )

        return updated

    def list_pending_payment_operations(
        self,
        repair_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if repair_id:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM payment_operations
                    WHERE repair_id = ?
                      AND completed_at IS NULL
                      AND operation_status NOT IN (
                          'COMPLETED',
                          'FAILED',
                          'REJECTED',
                          'CANCELED',
                          'CANCELLED'
                      )
                    ORDER BY created_at
                    """,
                    (repair_id,),
                ).fetchall()

            else:
                rows = connection.execute("""
                    SELECT *
                    FROM payment_operations
                    WHERE completed_at IS NULL
                      AND operation_status NOT IN (
                          'COMPLETED',
                          'FAILED',
                          'REJECTED',
                          'CANCELED',
                          'CANCELLED'
                      )
                    ORDER BY created_at
                    """).fetchall()

        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # UPDATE PAYMENT
    # ---------------------------------------------------------

    def update_payment(
        self,
        payment_id: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        current = self.get_payment(payment_id)

        if current is None:
            raise ValueError(f"Payment not found: {payment_id}")

        payment_status = self._optional_text(
            values.get(
                "payment_status",
                current["payment_status"],
            )
        ) or str(current["payment_status"])

        payment_method = self._optional_text(
            values.get(
                "payment_method",
                current["payment_method"],
            )
        ) or str(current["payment_method"])

        amount = self._required_amount(
            values.get(
                "amount",
                current["amount"],
            )
        )

        currency = (
            self._optional_text(
                values.get(
                    "currency",
                    current["currency"],
                )
            )
            or self.default_currency
        ).upper()

        payment_timestamp = (
            self._optional_text(
                values.get(
                    "payment_timestamp",
                    current["payment_timestamp"],
                )
            )
            or datetime.now(UTC).isoformat()
        )

        reference_number = self._optional_text(
            values.get(
                "reference_number",
                current["reference_number"],
            )
        )

        square_payment_id = self._optional_text(
            values.get(
                "square_payment_id",
                current["square_payment_id"],
            )
        )

        square_order_id = self._optional_text(
            values.get(
                "square_order_id",
                current["square_order_id"],
            )
        )

        square_terminal_checkout_id = self._optional_text(
            values.get(
                "square_terminal_checkout_id",
                current["square_terminal_checkout_id"],
            )
        )

        square_receipt_url = self._optional_text(
            values.get(
                "square_receipt_url",
                current["square_receipt_url"],
            )
        )

        notes = self._optional_text(
            values.get(
                "notes",
                current["notes"],
            )
        )

        self.create_write_backup()

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE repair_payments
                SET
                    payment_status = ?,
                    payment_method = ?,
                    amount = ?,
                    currency = ?,
                    payment_timestamp = ?,
                    reference_number = ?,
                    square_payment_id = ?,
                    square_order_id = ?,
                    square_terminal_checkout_id = ?,
                    square_receipt_url = ?,
                    notes = ?
                WHERE payment_id = ?
                """,
                (
                    payment_status,
                    payment_method,
                    amount,
                    currency,
                    payment_timestamp,
                    reference_number or None,
                    square_payment_id or None,
                    square_order_id or None,
                    square_terminal_checkout_id or None,
                    square_receipt_url or None,
                    notes or None,
                    payment_id,
                ),
            )

            connection.commit()

        updated = self.get_payment(payment_id)

        if updated is None:
            raise RuntimeError("Payment was updated but could not be reloaded.")

        return updated

    # ---------------------------------------------------------
    # PAYMENT TOTALS
    # ---------------------------------------------------------

    def amount_paid(
        self,
        repair_id: str,
    ) -> float:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        self._require_repair(repair_id)

        with self.connect() as connection:
            row = connection.execute(
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

        if row is None:
            return 0.0

        return round(
            float(row["total_paid"] or 0),
            2,
        )

    def refunded_amount(
        self,
        repair_id: str,
    ) -> float:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        self._require_repair(repair_id)

        with self.connect() as connection:
            row = connection.execute(
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

        if row is None:
            return 0.0

        return round(
            float(row["total_refunded"] or 0),
            2,
        )

    def refunded_amount_for_square_payment(
        self,
        repair_id: str,
        square_payment_id: str,
    ) -> float:
        repair_id = self._required_text(
            repair_id,
            "Repair ID",
        )

        square_payment_id = self._required_text(
            square_payment_id,
            "Square payment ID",
        )

        self._require_repair(repair_id)

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COALESCE(
                        SUM(refund_amount),
                        0.0
                    ) AS total_refunded
                FROM (
                    SELECT
                        MAX(amount) AS refund_amount
                    FROM repair_payments
                    WHERE repair_id = ?
                      AND payment_method = 'Square Refund'
                      AND payment_status IN (
                          'Refunded',
                          'Partially Refunded'
                      )
                      AND refunded_square_payment_id = ?
                    GROUP BY COALESCE(
                        square_refund_id,
                        reference_number,
                        payment_id
                    )
                )
                """,
                (
                    repair_id,
                    square_payment_id,
                ),
            ).fetchone()

        if row is None:
            return 0.0

        return round(
            float(row["total_refunded"] or 0.0),
            2,
        )

    def remaining_refundable_amount(
        self,
        repair_id: str,
        payment: dict[str, Any],
    ) -> float:
        square_payment_id = self._required_text(
            payment.get("square_payment_id"),
            "Square payment ID",
        )

        original_amount = self._required_amount(payment.get("amount"))

        refunded = self.refunded_amount_for_square_payment(
            repair_id,
            square_payment_id,
        )

        remaining = original_amount - refunded

        return round(
            max(
                remaining,
                0.0,
            ),
            2,
        )

    def net_amount_paid(
        self,
        repair_id: str,
    ) -> float:
        return round(
            self.amount_paid(repair_id) - self.refunded_amount(repair_id),
            2,
        )

    def amount_due(
        self,
        repair_id: str,
    ) -> float:
        repair = self._require_repair(repair_id)

        final_cost = repair.get("final_cost")

        if final_cost is None:
            return 0.0

        try:
            amount = float(final_cost)
        except (TypeError, ValueError):
            return 0.0

        return round(
            max(
                amount,
                0.0,
            ),
            2,
        )

    def balance_due(
        self,
        repair_id: str,
    ) -> float:
        balance = self.amount_due(repair_id) - self.net_amount_paid(repair_id)

        return round(
            max(
                balance,
                0.0,
            ),
            2,
        )

    def payment_status(
        self,
        repair_id: str,
    ) -> str:
        amount_due = self.amount_due(repair_id)

        amount_paid = self.net_amount_paid(repair_id)

        if amount_due <= 0:
            return "No Balance"

        if amount_paid <= 0:
            return "Unpaid"

        if amount_paid < amount_due:
            return "Partially Paid"

        return "Paid"

    def payment_summary(
        self,
        repair_id: str,
    ) -> dict[str, Any]:
        repair = self._require_repair(repair_id)

        final_cost = self.amount_due(repair_id)

        amount_paid = self.net_amount_paid(repair_id)

        balance_due = round(
            max(
                final_cost - amount_paid,
                0.0,
            ),
            2,
        )

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
            "payment_status": self.payment_status(repair_id),
            "currency": self.default_currency,
        }

    # ---------------------------------------------------------
    # CASH PAYMENTS
    # ---------------------------------------------------------

    def record_cash_payment(
        self,
        repair_id: str,
        *,
        amount: float,
        reference_number: str = "",
        notes: str = "",
        created_by: str = "",
    ) -> dict[str, Any]:
        return self.create_payment(
            repair_id,
            {
                "payment_status": "Completed",
                "payment_method": "Cash",
                "amount": amount,
                "currency": self.default_currency,
                "reference_number": reference_number,
                "notes": notes,
                "created_by": created_by,
            },
        )

    # ---------------------------------------------------------
    # EXTERNAL PAYMENTS
    # ---------------------------------------------------------

    def record_external_payment(
        self,
        repair_id: str,
        *,
        amount: float,
        payment_method: str,
        reference_number: str = "",
        notes: str = "",
        created_by: str = "",
    ) -> dict[str, Any]:
        payment_method = self._required_text(
            payment_method,
            "Payment method",
        )

        return self.create_payment(
            repair_id,
            {
                "payment_status": "Completed",
                "payment_method": payment_method,
                "amount": amount,
                "currency": self.default_currency,
                "reference_number": reference_number,
                "notes": notes,
                "created_by": created_by,
            },
        )

    # ---------------------------------------------------------
    # SQUARE PAYMENTS
    # ---------------------------------------------------------

    def record_square_payment(
        self,
        repair_id: str,
        *,
        amount: float,
        square_payment_id: str,
        square_order_id: str = "",
        square_terminal_checkout_id: str = "",
        square_receipt_url: str = "",
        payment_status: str = "Completed",
        reference_number: str = "",
        notes: str = "",
        created_by: str = "",
    ) -> dict[str, Any]:
        square_payment_id = self._required_text(
            square_payment_id,
            "Square payment ID",
        )

        existing = self.get_payment_by_square_id(square_payment_id)

        if existing is not None:
            return existing

        return self.create_payment(
            repair_id,
            {
                "payment_status": payment_status,
                "payment_method": "Square",
                "amount": amount,
                "currency": self.default_currency,
                "reference_number": reference_number,
                "square_payment_id": square_payment_id,
                "square_order_id": square_order_id,
                "square_terminal_checkout_id": square_terminal_checkout_id,
                "square_receipt_url": square_receipt_url,
                "notes": notes,
                "created_by": created_by,
            },
        )

    def record_square_refund(
        self,
        repair_id: str,
        *,
        amount: float,
        square_payment_id: str,
        square_refund_id: str,
        refund_status: str = "Refunded",
        notes: str = "",
        created_by: str = "",
    ) -> dict[str, Any]:
        square_payment_id = self._required_text(
            square_payment_id,
            "Square payment ID",
        )

        square_refund_id = self._required_text(
            square_refund_id,
            "Square refund ID",
        )

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_payments
                WHERE square_refund_id = ?
                LIMIT 1
                """,
                (square_refund_id,),
            ).fetchone()

        if row is not None:
            return dict(row)

        return self.create_payment(
            repair_id,
            {
                "payment_status": refund_status,
                "payment_method": "Square Refund",
                "amount": amount,
                "currency": self.default_currency,
                "reference_number": square_refund_id,
                "square_payment_id": None,
                "square_refund_id": square_refund_id,
                "refunded_square_payment_id": (square_payment_id),
                "notes": (
                    notes.strip()
                    or ("Refund for Square payment " f"{square_payment_id}")
                ),
                "created_by": created_by,
            },
        )

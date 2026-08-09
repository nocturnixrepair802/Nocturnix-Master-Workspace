from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

_ALLOWED_TABLES = {
    "devices",
    "services",
    "pricing_records",
    "integration_map",
}


def _pick(
    record: dict[str, Any],
    *names: str,
    default: Any = "",
) -> Any:
    for name in names:
        if name not in record:
            continue

        value = record[name]

        if value is not None:
            return value

    return default


class CatalogDatabase:
    """Read-only access to the imported Nocturnix catalog database."""

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(f"Catalog database not found: {self.database_path}")

        self.validate()

    def connect(
        self,
    ) -> sqlite3.Connection:
        database_uri = self.database_path.resolve().as_uri() + "?mode=ro"

        connection = sqlite3.connect(
            database_uri,
            uri=True,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        return connection

    def validate(
        self,
    ) -> None:
        with self.connect() as connection:
            tables = {
                str(row["name"])
                for row in connection.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """).fetchall()
            }

        missing = {
            "devices",
            "services",
            "pricing_records",
        } - tables

        if missing:
            names = ", ".join(sorted(missing))

            raise RuntimeError(f"Catalog database is missing required tables: {names}")

    def table_columns(
        self,
        table: str,
    ) -> list[str]:
        self._validate_table(table)

        with self.connect() as connection:
            rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()

        return [str(row["name"]) for row in rows]

    def table_counts(
        self,
    ) -> dict[str, int]:
        counts: dict[str, int] = {}

        with self.connect() as connection:
            for table in sorted(_ALLOWED_TABLES):
                exists = connection.execute(
                    """
                        SELECT 1
                        FROM sqlite_master
                        WHERE type = 'table'
                          AND name = ?
                        """,
                    (table,),
                ).fetchone()

                if exists is None:
                    continue

                row = connection.execute(f"""
                    SELECT COUNT(*) AS total
                    FROM "{table}"
                    """).fetchone()

                counts[table] = int(row["total"])

        return counts

    def list_devices(
        self,
        *,
        search: str = "",
        manufacturer_id: str | None = None,
        limit: int = 250,
    ) -> list[dict[str, Any]]:
        resolved_limit = max(
            1,
            min(
                int(limit),
                1000,
            ),
        )

        conditions = [
            "active = 1",
        ]

        parameters: list[Any] = []

        if manufacturer_id:
            conditions.append("manufacturer_id = ?")

            parameters.append(manufacturer_id)

        if search:
            conditions.append("""
                (
                    manufacturer LIKE ?
                    OR model LIKE ?
                    OR device_id LIKE ?
                )
                """)

            value = f"%{search.strip()}%"

            parameters.extend(
                [
                    value,
                    value,
                    value,
                ]
            )

        where_clause = " AND ".join(conditions)

        parameters.append(resolved_limit)

        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM devices
                WHERE {where_clause}
                ORDER BY manufacturer,
                        model
                LIMIT ?
                """,
                parameters,
            ).fetchall()

        return [self._normalize_device(dict(row)) for row in rows]

    def get_device(
        self,
        device_id: str,
    ) -> dict[str, Any] | None:
        records = self._all_records("devices")

        for record in records:
            normalized = self._normalize_device(record)

            if str(normalized["device_id"]) == str(device_id):
                return normalized

        return None

    def list_services(
        self,
        *,
        search: str = "",
        device_id: str | None = None,
        limit: int = 250,
    ) -> list[dict[str, Any]]:
        if device_id:
            with self.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT DISTINCT s.*
                    FROM services AS s
                    INNER JOIN pricing_records AS p
                        ON p.service_id = s.service_id
                    WHERE p.device_id = ?
                      AND s.active = 1
                    ORDER BY s.public_name,
                            s.internal_name
                    LIMIT ?
                    """,
                    (
                        device_id,
                        max(
                            1,
                            min(
                                int(limit),
                                1000,
                            ),
                        ),
                    ),
                ).fetchall()

            records = [dict(row) for row in rows]
        else:
            records = self._search_table(
                "services",
                search=search,
                limit=limit,
            )

        normalized = [self._normalize_service(record) for record in records]

        if search and device_id:
            needle = search.casefold()

            normalized = [
                record
                for record in normalized
                if needle in str(record["service_name"]).casefold()
                or needle in str(record["service_type"]).casefold()
            ]

        return normalized

    def list_pricing(
        self,
        *,
        search: str = "",
        service_id: str | None = None,
        device_id: str | None = None,
        limit: int = 250,
    ) -> list[dict[str, Any]]:
        resolved_limit = max(
            1,
            min(
                int(limit),
                1000,
            ),
        )

        conditions: list[str] = []
        parameters: list[Any] = []

        if service_id:
            conditions.append("p.service_id = ?")
            parameters.append(service_id)

        if device_id:
            conditions.append("p.device_id = ?")
            parameters.append(device_id)

        if search:
            conditions.append(
                """
                (
                    CAST(p.service_id AS TEXT) LIKE ?
                    OR CAST(p.device_id AS TEXT) LIKE ?
                    OR CAST(s.public_name AS TEXT) LIKE ?
                    OR CAST(s.internal_name AS TEXT) LIKE ?
                )
                """
            )

            value = f"%{search.strip()}%"

            parameters.extend(
                [
                    value,
                    value,
                    value,
                    value,
                ]
            )

        where_clause = ""

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        parameters.append(resolved_limit)

        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    p.*,
                    s.public_name,
                    s.internal_name
                FROM pricing_records AS p
                LEFT JOIN services AS s
                    ON s.service_id = p.service_id
                {where_clause}
                ORDER BY p.device_id,
                        s.public_name,
                        p.service_id
                LIMIT ?
                """,
                parameters,
            ).fetchall()

        results: list[dict[str, Any]] = []

        for row in rows:
            raw = dict(row)

            normalized = self._normalize_pricing(raw)

            normalized["service_name"] = _pick(
                raw,
                "public_name",
                "internal_name",
            )

            results.append(normalized)

        return results

    def schema(
        self,
    ) -> dict[
        str,
        list[str],
    ]:
        result: dict[
            str,
            list[str],
        ] = {}

        with self.connect() as connection:
            existing = {
                str(row["name"])
                for row in connection.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """).fetchall()
            }

        for table in sorted(_ALLOWED_TABLES):
            if table not in existing:
                continue

            result[table] = self.table_columns(table)

        return result

    def _search_table(
        self,
        table: str,
        *,
        search: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        self._validate_table(table)

        resolved_limit = max(
            1,
            min(
                int(limit),
                1000,
            ),
        )

        columns = self.table_columns(table)

        with self.connect() as connection:
            if not search:
                rows = connection.execute(
                    f"""
                    SELECT *
                    FROM "{table}"
                    LIMIT ?
                    """,
                    (resolved_limit,),
                ).fetchall()

                return [dict(row) for row in rows]

            search_value = f"%{search.strip()}%"

            conditions = [(f'CAST("{column}" AS TEXT) LIKE ?') for column in columns]

            where_clause = " OR ".join(conditions)

            parameters: list[Any] = [search_value for _ in columns]

            parameters.append(resolved_limit)

            rows = connection.execute(
                f"""
                SELECT *
                FROM "{table}"
                WHERE {where_clause}
                LIMIT ?
                """,
                parameters,
            ).fetchall()

        return [dict(row) for row in rows]

    def list_manufacturers(
        self,
    ) -> list[dict[str, str]]:
        with self.connect() as connection:
            rows = connection.execute("""
                SELECT DISTINCT
                    manufacturer_id,
                    manufacturer
                FROM devices
                WHERE active = 1
                  AND manufacturer IS NOT NULL
                  AND TRIM(manufacturer) <> ''
                ORDER BY manufacturer
                """).fetchall()

        return [
            {
                "manufacturer_id": str(row["manufacturer_id"] or ""),
                "manufacturer": str(row["manufacturer"] or ""),
            }
            for row in rows
        ]

    def _all_records(
        self,
        table: str,
    ) -> list[dict[str, Any]]:
        self._validate_table(table)

        with self.connect() as connection:
            rows = connection.execute(f"""
                SELECT *
                FROM "{table}"
                """).fetchall()

        return [dict(row) for row in rows]

    @staticmethod
    def _normalize_device(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "device_id": _pick(
                record,
                "device_id",
            ),
            "device_type_id": _pick(
                record,
                "device_type_id",
            ),
            "manufacturer_id": _pick(
                record,
                "manufacturer_id",
            ),
            "manufacturer": _pick(
                record,
                "manufacturer",
            ),
            "device_family_id": _pick(
                record,
                "device_family_id",
            ),
            "device_family": "",
            "device_model_id": "",
            "device_model": _pick(
                record,
                "model",
            ),
            "active": bool(
                _pick(
                    record,
                    "active",
                    default=True,
                )
            ),
        }

    @staticmethod
    def _normalize_service(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        service_name = _pick(
            record,
            "public_name",
            "internal_name",
        )

        return {
            "service_id": _pick(
                record,
                "service_id",
            ),
            "service_name": service_name,
            "device_id": "",
            "manufacturer": "",
            "device_model": "",
            "service_type_id": _pick(
                record,
                "service_type_id",
            ),
            "service_type": _pick(
                record,
                "service_type_name",
            ),
            "status": (
                "active"
                if bool(
                    _pick(
                        record,
                        "active",
                        default=True,
                    )
                )
                else "inactive"
            ),
        }

    @staticmethod
    def _normalize_pricing(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        part_cost_cents = _pick(
            record,
            "part_cost_cents",
            default=None,
        )

        retail_price_cents = _pick(
            record,
            "retail_price_cents",
            default=None,
        )

        part_cost = (
            float(part_cost_cents) / 100 if part_cost_cents is not None else None
        )

        price = (
            float(retail_price_cents) / 100 if retail_price_cents is not None else None
        )

        return {
            "service_id": _pick(
                record,
                "service_id",
            ),
            "service_name": "",
            "device_id": _pick(
                record,
                "device_id",
            ),
            "legacy_price": None,
            "part_cost": part_cost,
            "labor_hours": None,
            "labor_rate": None,
            "price": price,
            "status": _pick(
                record,
                "approval_status",
            ),
        }

    @staticmethod
    def _validate_table(
        table: str,
    ) -> None:
        if table not in _ALLOWED_TABLES:
            raise ValueError(f"Unsupported catalog table: {table}")

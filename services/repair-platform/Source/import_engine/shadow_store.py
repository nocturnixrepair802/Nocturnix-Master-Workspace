"""SQLite shadow persistence isolated from production runtime storage."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path
from typing import Any

from import_engine.manifest import ImportManifest
from import_engine.workbook import SourceRow, canonical_row_json

PROVENANCE_COLUMNS = """
    import_release_id TEXT NOT NULL,
    source_workbook TEXT NOT NULL,
    approved_version TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    source_worksheet TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_row_identifier TEXT NOT NULL,
    source_row_number INTEGER NOT NULL,
    imported_at_utc TEXT NOT NULL,
    source_review_status TEXT NOT NULL,
    status_class TEXT NOT NULL,
    imported_status TEXT NOT NULL CHECK (imported_status = 'SHADOW_REFERENCE'),
    effective_at_utc TEXT,
    superseded_version TEXT,
    activation_approved INTEGER NOT NULL DEFAULT 0 CHECK (activation_approved = 0),
    runtime_active INTEGER NOT NULL DEFAULT 0 CHECK (runtime_active = 0),
    source_row_sha256 TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    FOREIGN KEY (import_release_id) REFERENCES shadow_import_releases(import_release_id),
    UNIQUE (import_release_id, source_row_identifier)
"""

SCHEMA = f"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shadow_import_releases (
    import_release_id TEXT PRIMARY KEY,
    contract_version TEXT NOT NULL,
    workbook_version TEXT NOT NULL,
    workbook_sha256 TEXT NOT NULL,
    source_workbook TEXT NOT NULL,
    imported_at_utc TEXT NOT NULL,
    import_status TEXT NOT NULL CHECK (
        import_status IN ('IMPORTING', 'COMPLETED', 'FAILED', 'ROLLED_BACK')
    ),
    activation_allowed INTEGER NOT NULL DEFAULT 0 CHECK (activation_allowed = 0),
    runtime_records_activated INTEGER NOT NULL DEFAULT 0
        CHECK (runtime_records_activated = 0),
    manifest_json TEXT,
    rollback_token TEXT NOT NULL,
    UNIQUE (contract_version, workbook_version, workbook_sha256)
);

CREATE TABLE IF NOT EXISTS shadow_canonical_service_types (
    import_row_id INTEGER PRIMARY KEY,
    canonical_service_type_id TEXT NOT NULL,
    service_category TEXT,
    service_type TEXT NOT NULL,
    service_description TEXT,
    applies_to TEXT,
    estimated_time_min REAL,
    default_warranty_days REAL,
    taxable TEXT,
    source_active TEXT,
    internal_notes TEXT,
    identity_authority TEXT,
    reviewer_notes TEXT,
    {PROVENANCE_COLUMNS}
);

CREATE TABLE IF NOT EXISTS shadow_service_type_aliases (
    import_row_id INTEGER PRIMARY KEY,
    alias_id TEXT NOT NULL,
    source_system TEXT,
    source_field TEXT,
    source_value TEXT,
    normalized_source_value TEXT,
    proposed_canonical_service_type_id TEXT,
    proposed_canonical_service_type TEXT,
    alias_rule_type TEXT,
    evidence TEXT,
    confidence TEXT,
    reviewer TEXT,
    reviewer_notes TEXT,
    {PROVENANCE_COLUMNS}
);

CREATE TABLE IF NOT EXISTS shadow_service_normalization (
    import_row_id INTEGER PRIMARY KEY,
    service_id TEXT NOT NULL,
    service_name TEXT,
    current_repair_type_id TEXT,
    current_repair_type TEXT,
    manufacturer_id TEXT,
    manufacturer_name TEXT,
    device_family_code TEXT,
    device_family_name TEXT,
    proposed_canonical_service_type_id TEXT,
    proposed_canonical_service_type TEXT,
    mapping_method TEXT,
    mapping_evidence TEXT,
    confidence TEXT,
    reviewer_notes TEXT,
    {PROVENANCE_COLUMNS}
);

CREATE TABLE IF NOT EXISTS shadow_labor_normalization (
    import_row_id INTEGER PRIMARY KEY,
    labor_standard_id TEXT NOT NULL,
    legacy_labor_id TEXT,
    labor_name TEXT,
    current_repair_type TEXT,
    device_family_code TEXT,
    device_family TEXT,
    manufacturer_id TEXT,
    manufacturer TEXT,
    proposed_canonical_service_type_id TEXT,
    proposed_canonical_service_type TEXT,
    mapping_method TEXT,
    mapping_evidence TEXT,
    confidence TEXT,
    reviewer_notes TEXT,
    {PROVENANCE_COLUMNS}
);
"""


class ShadowStore:
    """Own a SQLite database containing shadow data and no runtime access path."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        """Create a constrained connection to the caller-selected shadow database."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def install_schema(self) -> None:
        """Install only namespaced shadow tables."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            with connection:
                connection.executescript(SCHEMA)

    def completed_manifest(
        self,
        *,
        contract_version: str,
        workbook_version: str,
        workbook_sha256: str,
    ) -> dict[str, Any] | None:
        """Return a prior completed manifest for the idempotency key."""
        if not self.database_path.exists():
            return None
        with closing(self.connect()) as connection:
            row = connection.execute(
                """
                SELECT manifest_json
                FROM shadow_import_releases
                WHERE contract_version = ?
                  AND workbook_version = ?
                  AND workbook_sha256 = ?
                  AND import_status = 'COMPLETED'
                """,
                (contract_version, workbook_version, workbook_sha256),
            ).fetchone()
        return json.loads(row["manifest_json"]) if row and row["manifest_json"] else None

    def import_release(
        self,
        manifest: ImportManifest,
        rows_by_worksheet: dict[str, tuple[SourceRow, ...]],
    ) -> None:
        """Atomically insert a release and all shadow rows."""
        self.install_schema()
        with closing(self.connect()) as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    """
                    SELECT import_status
                    FROM shadow_import_releases
                    WHERE contract_version = ?
                      AND workbook_version = ?
                      AND workbook_sha256 = ?
                    """,
                    (
                        manifest.contract_version,
                        manifest.workbook_version,
                        manifest.workbook_sha256,
                    ),
                ).fetchone()
                if existing:
                    if existing["import_status"] == "COMPLETED":
                        return
                    raise ValueError(
                        "An incomplete import already owns this release key"
                    )

                connection.execute(
                    """
                    INSERT INTO shadow_import_releases (
                        import_release_id, contract_version, workbook_version,
                        workbook_sha256, source_workbook, imported_at_utc,
                        import_status, activation_allowed,
                        runtime_records_activated, rollback_token
                    ) VALUES (?, ?, ?, ?, ?, ?, 'IMPORTING', 0, 0, ?)
                    """,
                    (
                        manifest.release_id,
                        manifest.contract_version,
                        manifest.workbook_version,
                        manifest.workbook_sha256,
                        manifest.workbook_path,
                        manifest.imported_at_utc,
                        manifest.rollback_metadata.rollback_token,
                    ),
                )
                self._insert_canonical(
                    connection,
                    manifest,
                    rows_by_worksheet["01 - Canonical Service Types"],
                )
                self._insert_aliases(
                    connection,
                    manifest,
                    rows_by_worksheet["02 - Service Type Aliases"],
                )
                self._insert_services(
                    connection,
                    manifest,
                    rows_by_worksheet["03 - Service Normalization"],
                )
                self._insert_labor(
                    connection,
                    manifest,
                    rows_by_worksheet["04 - Labor Normalization"],
                )
                connection.execute(
                    """
                    UPDATE shadow_import_releases
                    SET import_status = 'COMPLETED', manifest_json = ?
                    WHERE import_release_id = ?
                    """,
                    (
                        json.dumps(
                            manifest.to_dict(),
                            ensure_ascii=False,
                            separators=(",", ":"),
                            sort_keys=True,
                        ),
                        manifest.release_id,
                    ),
                )

    @staticmethod
    def _provenance(
        manifest: ImportManifest, row: SourceRow
    ) -> tuple[Any, ...]:
        return (
            manifest.release_id,
            manifest.workbook_path,
            manifest.workbook_version,
            manifest.workbook_sha256,
            row.worksheet,
            row.table,
            row.source_row_identifier,
            row.excel_row,
            manifest.imported_at_utc,
            row.source_status,
            row.status_class,
            row.imported_status,
            None,
            None,
            0,
            0,
            row.row_sha256,
            canonical_row_json(row.values),
        )

    @staticmethod
    def _execute_many(
        connection: sqlite3.Connection,
        statement: str,
        rows: Iterable[tuple[Any, ...]],
    ) -> None:
        connection.executemany(statement, rows)

    def _insert_canonical(
        self,
        connection: sqlite3.Connection,
        manifest: ImportManifest,
        rows: tuple[SourceRow, ...],
    ) -> None:
        statement = """
            INSERT INTO shadow_canonical_service_types (
                canonical_service_type_id, service_category, service_type,
                service_description, applies_to, estimated_time_min,
                default_warranty_days, taxable, source_active, internal_notes,
                identity_authority, reviewer_notes,
                import_release_id, source_workbook, approved_version,
                source_sha256, source_worksheet, source_table,
                source_row_identifier, source_row_number, imported_at_utc,
                source_review_status, status_class, imported_status,
                effective_at_utc, superseded_version, activation_approved,
                runtime_active, source_row_sha256, raw_payload
            ) VALUES ({})
        """.format(",".join("?" for _ in range(30)))
        self._execute_many(
            connection,
            statement,
            (
                (
                    row.values["Proposed Canonical Service Type ID"],
                    row.values["Service Category"],
                    row.values["Service Type"],
                    row.values["Service Description"],
                    row.values["Applies To"],
                    row.values["Estimated Time (Min)"],
                    row.values["Default Warranty (Days)"],
                    row.values["Taxable"],
                    row.values["Active"],
                    row.values["Internal Notes"],
                    row.values["Identity Authority"],
                    row.values["Reviewer Notes"],
                    *self._provenance(manifest, row),
                )
                for row in rows
            ),
        )

    def _insert_aliases(
        self,
        connection: sqlite3.Connection,
        manifest: ImportManifest,
        rows: tuple[SourceRow, ...],
    ) -> None:
        statement = """
            INSERT INTO shadow_service_type_aliases (
                alias_id, source_system, source_field, source_value,
                normalized_source_value, proposed_canonical_service_type_id,
                proposed_canonical_service_type, alias_rule_type, evidence,
                confidence, reviewer, reviewer_notes,
                import_release_id, source_workbook, approved_version,
                source_sha256, source_worksheet, source_table,
                source_row_identifier, source_row_number, imported_at_utc,
                source_review_status, status_class, imported_status,
                effective_at_utc, superseded_version, activation_approved,
                runtime_active, source_row_sha256, raw_payload
            ) VALUES ({})
        """.format(",".join("?" for _ in range(30)))
        self._execute_many(
            connection,
            statement,
            (
                (
                    row.values["Alias ID"],
                    row.values["Source System"],
                    row.values["Source Field"],
                    row.values["Source Value"],
                    row.values["Normalized Source Value"],
                    row.values["Proposed Canonical Service Type ID"],
                    row.values["Proposed Canonical Service Type"],
                    row.values["Alias Rule Type"],
                    row.values["Evidence"],
                    row.values["Confidence"],
                    row.values["Reviewer"],
                    row.values["Reviewer Notes"],
                    *self._provenance(manifest, row),
                )
                for row in rows
            ),
        )

    def _insert_services(
        self,
        connection: sqlite3.Connection,
        manifest: ImportManifest,
        rows: tuple[SourceRow, ...],
    ) -> None:
        statement = """
            INSERT INTO shadow_service_normalization (
                service_id, service_name, current_repair_type_id,
                current_repair_type, manufacturer_id, manufacturer_name,
                device_family_code, device_family_name,
                proposed_canonical_service_type_id,
                proposed_canonical_service_type, mapping_method,
                mapping_evidence, confidence, reviewer_notes,
                import_release_id, source_workbook, approved_version,
                source_sha256, source_worksheet, source_table,
                source_row_identifier, source_row_number, imported_at_utc,
                source_review_status, status_class, imported_status,
                effective_at_utc, superseded_version, activation_approved,
                runtime_active, source_row_sha256, raw_payload
            ) VALUES ({})
        """.format(",".join("?" for _ in range(32)))
        self._execute_many(
            connection,
            statement,
            (
                (
                    row.values["Service ID"],
                    row.values["Service Name"],
                    row.values["Current Repair Type ID"],
                    row.values["Current Repair Type"],
                    row.values["Manufacturer ID"],
                    row.values["Manufacturer Name"],
                    row.values["Device Family Code"],
                    row.values["Device Family Name"],
                    row.values["Proposed Canonical Service Type ID"],
                    row.values["Proposed Canonical Service Type"],
                    row.values["Mapping Method"],
                    row.values["Mapping Evidence"],
                    row.values["Confidence"],
                    row.values["Reviewer Notes"],
                    *self._provenance(manifest, row),
                )
                for row in rows
            ),
        )

    def _insert_labor(
        self,
        connection: sqlite3.Connection,
        manifest: ImportManifest,
        rows: tuple[SourceRow, ...],
    ) -> None:
        statement = """
            INSERT INTO shadow_labor_normalization (
                labor_standard_id, legacy_labor_id, labor_name,
                current_repair_type, device_family_code, device_family,
                manufacturer_id, manufacturer,
                proposed_canonical_service_type_id,
                proposed_canonical_service_type, mapping_method,
                mapping_evidence, confidence, reviewer_notes,
                import_release_id, source_workbook, approved_version,
                source_sha256, source_worksheet, source_table,
                source_row_identifier, source_row_number, imported_at_utc,
                source_review_status, status_class, imported_status,
                effective_at_utc, superseded_version, activation_approved,
                runtime_active, source_row_sha256, raw_payload
            ) VALUES ({})
        """.format(",".join("?" for _ in range(32)))
        self._execute_many(
            connection,
            statement,
            (
                (
                    row.values["Labor Standard ID"],
                    row.values["Legacy Labor ID"],
                    row.values["Labor Name"],
                    row.values["Current Repair Type"],
                    row.values["Device Family Code"],
                    row.values["Device Family"],
                    row.values["Manufacturer ID"],
                    row.values["Manufacturer"],
                    row.values["Proposed Canonical Service Type ID"],
                    row.values["Proposed Canonical Service Type"],
                    row.values["Mapping Method"],
                    row.values["Mapping Evidence"],
                    row.values["Confidence"],
                    row.values["Reviewer Notes"],
                    *self._provenance(manifest, row),
                )
                for row in rows
            ),
        )

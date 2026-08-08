"""Application-independent orchestration for approved shadow imports."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from import_engine.contract import (
    APPROVED_SHA256,
    APPROVED_VERSION,
    CONTRACT_VERSION,
)
from import_engine.manifest import (
    ImportManifest,
    ImportState,
    RollbackMetadata,
    ValidationSummary,
)
from import_engine.shadow_store import ShadowStore
from import_engine.workbook import (
    ApprovedWorkbookValidator,
    WorkbookContractError,
    file_sha256,
)


class ImportEngineError(RuntimeError):
    """Public error raised when an import fails closed."""


class ImportEngine:
    """Validate one approved release and import it only into shadow tables."""

    def __init__(
        self,
        *,
        workbook_path: str | Path,
        shadow_store: ShadowStore,
        workbook_version: str = APPROVED_VERSION,
        expected_sha256: str = APPROVED_SHA256,
        clock: Callable[[], datetime] | None = None,
    ):
        self.workbook_path = Path(workbook_path)
        self.shadow_store = shadow_store
        self.workbook_version = workbook_version
        self.expected_sha256 = expected_sha256.upper()
        self._clock = clock or (lambda: datetime.now(UTC))
        self.state = ImportState.CREATED

    def run(self) -> ImportManifest:
        """Run a fail-closed, idempotent shadow import."""
        if self.workbook_version != APPROVED_VERSION:
            raise ImportEngineError(
                f"Unsupported approved workbook version: {self.workbook_version}"
            )
        if self.state is not ImportState.CREATED:
            raise ImportEngineError("An ImportEngine instance may run only once")

        try:
            observed_sha256 = file_sha256(self.workbook_path)
            if observed_sha256 != self.expected_sha256:
                raise WorkbookContractError(
                    "Workbook SHA-256 mismatch: "
                    f"expected {self.expected_sha256}, observed {observed_sha256}"
                )
            self.state = ImportState.HASH_VERIFIED
            prior = self.shadow_store.completed_manifest(
                contract_version=CONTRACT_VERSION,
                workbook_version=self.workbook_version,
                workbook_sha256=self.expected_sha256,
            )
            if prior is not None:
                self.state = ImportState.COMPLETED
                return self._manifest_from_dict(prior)

            validated = ApprovedWorkbookValidator(
                self.workbook_path, self.expected_sha256
            ).validate()
            self.state = ImportState.WORKBOOK_VALIDATED
            manifest = self._build_manifest(validated)
            self.state = ImportState.MANIFEST_BUILT
            self.state = ImportState.IMPORTING
            self.shadow_store.import_release(manifest, validated.import_rows)
            self.state = ImportState.COMPLETED
            return manifest
        except (OSError, ValueError, WorkbookContractError) as error:
            self.state = ImportState.FAILED
            raise ImportEngineError(f"Shadow import failed: {error}") from error

    def _build_manifest(self, validated) -> ImportManifest:
        imported_at = self._clock().astimezone(UTC).isoformat()
        release_key = (
            f"{CONTRACT_VERSION}|{self.workbook_version}|"
            f"{validated.workbook_sha256}"
        )
        release_id = str(uuid5(NAMESPACE_URL, release_key))
        rollback_token = str(uuid5(NAMESPACE_URL, f"rollback|{release_key}"))
        return ImportManifest(
            manifest_schema_version="1.0",
            contract_version=CONTRACT_VERSION,
            release_id=release_id,
            workbook_path=str(self.workbook_path.resolve()),
            workbook_version=self.workbook_version,
            workbook_sha256=validated.workbook_sha256,
            imported_at_utc=imported_at,
            import_status=ImportState.COMPLETED,
            row_counts=validated.row_counts,
            reconciliation_counts=validated.reconciliation_counts,
            validation_summary=validated.validation_summary,
            imported_worksheets=tuple(validated.import_rows),
            rollback_metadata=RollbackMetadata(
                supported=True,
                strategy=(
                    "Mark the shadow release ROLLED_BACK and exclude it from "
                    "reference views; no production records exist."
                ),
                prior_release_id=None,
                rollback_token=rollback_token,
            ),
            activation_allowed=False,
            runtime_records_activated=0,
            manifest_metadata={
                "import_mode": "SHADOW_REFERENCE",
                "idempotency_key": release_key,
                "source_read_mode": "read_only",
            },
        )

    @staticmethod
    def _manifest_from_dict(payload: dict) -> ImportManifest:
        validation = payload["validation_summary"]
        rollback = payload["rollback_metadata"]
        return ImportManifest(
            manifest_schema_version=payload["manifest_schema_version"],
            contract_version=payload["contract_version"],
            release_id=payload["release_id"],
            workbook_path=payload["workbook_path"],
            workbook_version=payload["workbook_version"],
            workbook_sha256=payload["workbook_sha256"],
            imported_at_utc=payload["imported_at_utc"],
            import_status=ImportState(payload["import_status"]),
            row_counts=dict(payload["row_counts"]),
            reconciliation_counts=dict(payload["reconciliation_counts"]),
            validation_summary=ValidationSummary(
                result=validation["result"],
                checks_passed=validation["checks_passed"],
                checks_failed=validation["checks_failed"],
                messages=tuple(validation["messages"]),
            ),
            imported_worksheets=tuple(payload["imported_worksheets"]),
            rollback_metadata=RollbackMetadata(
                supported=rollback["supported"],
                strategy=rollback["strategy"],
                prior_release_id=rollback["prior_release_id"],
                rollback_token=rollback["rollback_token"],
            ),
            activation_allowed=payload["activation_allowed"],
            runtime_records_activated=payload["runtime_records_activated"],
            manifest_metadata=dict(payload["manifest_metadata"]),
        )

    @staticmethod
    def manifest_json(manifest: ImportManifest) -> str:
        """Render a stable structured manifest for reports or external storage."""
        return json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

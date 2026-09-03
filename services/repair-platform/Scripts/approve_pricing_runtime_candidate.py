from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from services.pricing_rule_loader import (
    APPROVED_STATUS,
    SUPPORTED_SCHEMA_VERSION,
    PricingRuleLoader,
    PricingRuleLoadError,
)

CANDIDATE_STATUS = "CANDIDATE"


class PricingRuntimeApprovalError(RuntimeError):
    """Raised when a runtime pricing candidate cannot be safely approved."""


def read_candidate(
    path: Path,
) -> tuple[bytes, dict[str, Any]]:
    if not path.exists():
        raise PricingRuntimeApprovalError(f"Candidate artifact not found: {path}")

    if not path.is_file():
        raise PricingRuntimeApprovalError(
            "Candidate artifact path must point to a file."
        )

    try:
        candidate_bytes = path.read_bytes()
    except OSError as exc:
        raise PricingRuntimeApprovalError(
            "Candidate artifact could not be read."
        ) from exc

    try:
        payload = json.loads(candidate_bytes.decode("utf-8"))
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise PricingRuntimeApprovalError(
            "Candidate artifact must be valid UTF-8 JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise PricingRuntimeApprovalError("Candidate artifact root must be an object.")

    return candidate_bytes, payload


def sha256_bytes(
    value: bytes,
) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_candidate(
    payload: dict[str, Any],
) -> None:
    schema_version = str(payload.get("schema_version") or "").strip()

    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise PricingRuntimeApprovalError(
            f"Candidate has unsupported schema_version: {schema_version or '<blank>'}"
        )

    rule_set_id = str(payload.get("rule_set_id") or "").strip()

    if not rule_set_id:
        raise PricingRuntimeApprovalError("Candidate requires rule_set_id.")

    status = str(payload.get("status") or "").strip().upper()

    if status != CANDIDATE_STATUS:
        raise PricingRuntimeApprovalError(
            "Candidate artifact must have status CANDIDATE."
        )

    rules = payload.get("rules")

    if not isinstance(rules, list):
        raise PricingRuntimeApprovalError("Candidate field 'rules' must be a list.")

    if not rules:
        raise PricingRuntimeApprovalError(
            "Refusing to approve an empty pricing rule set."
        )

    identities: set[tuple[str, str]] = set()

    for index, rule in enumerate(
        rules,
        start=1,
    ):
        if not isinstance(rule, dict):
            raise PricingRuntimeApprovalError(
                f"Pricing rule #{index} must be an object."
            )

        service_type_id = str(rule.get("service_type_id") or "").strip()

        variant_key = str(rule.get("variant_key") or "BASE").strip().upper()

        if not service_type_id:
            raise PricingRuntimeApprovalError(
                f"Pricing rule #{index} requires service_type_id."
            )

        if not variant_key:
            variant_key = "BASE"

        identity = (
            service_type_id,
            variant_key,
        )

        if identity in identities:
            raise PricingRuntimeApprovalError(
                f"Duplicate candidate pricing identity: {identity[0]} / {identity[1]}"
            )

        identities.add(identity)


def build_approved_payload(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    approved = dict(candidate)

    approved["status"] = APPROVED_STATUS

    return approved


def serialize_payload(
    payload: dict[str, Any],
) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    ).encode("utf-8")


def validate_approved_artifact(
    path: Path,
    *,
    expected_rule_count: int,
) -> None:
    try:
        rules = PricingRuleLoader(path).load()
    except PricingRuleLoadError as exc:
        raise PricingRuntimeApprovalError(
            "Generated approved artifact failed runtime loader validation."
        ) from exc

    if len(rules) != expected_rule_count:
        raise PricingRuntimeApprovalError(
            "Generated approved artifact loaded an unexpected number of pricing rules."
        )


def approve_candidate(
    *,
    candidate_path: Path,
    output_path: Path,
    approval_record_path: Path,
    approved_by: str,
    confirm_approval: bool,
    approved_at: datetime | None = None,
) -> dict[str, Any]:
    if not confirm_approval:
        raise PricingRuntimeApprovalError("Explicit --confirm-approval is required.")

    approved_by = approved_by.strip()

    if not approved_by:
        raise PricingRuntimeApprovalError("Approver identity cannot be blank.")

    try:
        candidate_resolved = candidate_path.resolve()

        output_resolved = output_path.resolve()

        approval_resolved = approval_record_path.resolve()
    except OSError as exc:
        raise PricingRuntimeApprovalError("Could not resolve approval paths.") from exc

    if candidate_resolved == output_resolved:
        raise PricingRuntimeApprovalError(
            "Approved output must not overwrite the candidate artifact."
        )

    if candidate_resolved == approval_resolved:
        raise PricingRuntimeApprovalError(
            "Approval record must not overwrite the candidate artifact."
        )

    if output_resolved == approval_resolved:
        raise PricingRuntimeApprovalError(
            "Approved artifact and approval record must use different paths."
        )

    candidate_bytes, candidate = read_candidate(candidate_path)

    validate_candidate(candidate)

    candidate_hash = sha256_bytes(candidate_bytes)

    rules = candidate["rules"]

    approved_payload = build_approved_payload(candidate)

    approved_bytes = serialize_payload(approved_payload)

    approved_hash = sha256_bytes(approved_bytes)

    if approved_at is None:
        approved_at = datetime.now(UTC)

    if approved_at.tzinfo is None:
        raise PricingRuntimeApprovalError("Approval timestamp must be timezone-aware.")

    approved_at_utc = approved_at.astimezone(UTC)

    approval_record = {
        "schema_version": "1.0",
        "rule_set_id": str(candidate["rule_set_id"]).strip(),
        "candidate_sha256": (candidate_hash),
        "approved_artifact_sha256": (approved_hash),
        "approved_by": approved_by,
        "approved_at": (approved_at_utc.isoformat().replace("+00:00", "Z")),
        "rule_count": len(rules),
        "candidate_path": str(candidate_path),
        "approved_artifact_path": str(output_path),
    }

    approval_bytes = serialize_payload(approval_record)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    approval_record_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        raise PricingRuntimeApprovalError(
            "Approved runtime artifact already exists. Refusing to overwrite it."
        )

    if approval_record_path.exists():
        raise PricingRuntimeApprovalError(
            "Approval record already exists. Refusing to overwrite it."
        )

    output_written = False
    approval_written = False

    try:
        output_path.write_bytes(approved_bytes)

        output_written = True

        validate_approved_artifact(
            output_path,
            expected_rule_count=len(rules),
        )

        approval_record_path.write_bytes(approval_bytes)

        approval_written = True

    except Exception:
        if approval_written:
            approval_record_path.unlink(missing_ok=True)

        if output_written:
            output_path.unlink(missing_ok=True)

        raise

    return approval_record


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly approve a reviewed Nocturnix runtime pricing candidate."
        )
    )

    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--approval-record",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--approved-by",
        required=True,
    )

    parser.add_argument(
        "--confirm-approval",
        action="store_true",
        help=("Explicitly confirm governance approval of this pricing candidate."),
    )

    args = parser.parse_args()

    try:
        record = approve_candidate(
            candidate_path=args.candidate,
            output_path=args.output,
            approval_record_path=(args.approval_record),
            approved_by=args.approved_by,
            confirm_approval=(args.confirm_approval),
        )
    except PricingRuntimeApprovalError as exc:
        raise SystemExit(f"APPROVAL FAILED: {exc}") from exc

    print()
    print("=" * 72)
    print("Nocturnix Pricing Runtime Approval")
    print("=" * 72)

    print(
        "Rule set:",
        record["rule_set_id"],
    )

    print(
        "Rules approved:",
        record["rule_count"],
    )

    print(
        "Approved by:",
        record["approved_by"],
    )

    print(
        "Approved at:",
        record["approved_at"],
    )

    print()

    print(
        "Candidate SHA-256:",
        record["candidate_sha256"],
    )

    print(
        "Approved SHA-256:",
        record["approved_artifact_sha256"],
    )

    print()

    print(
        "Approved artifact:",
        args.output,
    )

    print(
        "Approval record:",
        args.approval_record,
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from Scripts.approve_pricing_runtime_candidate import (
    PricingRuntimeApprovalError,
    approve_candidate,
)

from services.pricing_rule_loader import (
    PricingRuleLoader,
)


def candidate_rule() -> dict[str, object]:
    return {
        "service_type_id": "STY000001",
        "service_type": "Screen Replacement",
        "service_category_id": "SC000010",
        "default_labor_hours": "1.00",
        "labor_profile_id": "LAB000002",
        "labor_tier": "L2 Standard",
        "hourly_rate": "100.00",
        "minimum_charge": "85.00",
        "target_margin": "0.30",
        "minimum_margin": "0.20",
        "overhead_rate": "0.12",
        "warranty_rate": "0.05",
        "risk_rate": "0.04",
        "processing_rate": "0.03",
        "rounding_rule": "End in .99",
        "variant_key": "BASE",
        "variant_name": None,
    }


def write_candidate(
    path: Path,
    *,
    status: str = "CANDIDATE",
) -> None:
    payload = {
        "schema_version": "1.0",
        "rule_set_id": "PRSET-CANDIDATE-TEST",
        "status": status,
        "rules": [
            candidate_rule(),
        ],
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_candidate_requires_explicit_confirmation(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(candidate)

    with pytest.raises(
        PricingRuntimeApprovalError,
        match="confirm-approval",
    ):
        approve_candidate(
            candidate_path=candidate,
            output_path=(tmp_path / "pricing_rules.json"),
            approval_record_path=(tmp_path / "approval.json"),
            approved_by="Test Approver",
            confirm_approval=False,
        )


def test_approval_does_not_modify_candidate(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(candidate)

    before = candidate.read_bytes()

    output = tmp_path / "pricing_rules.json"

    approval = tmp_path / "approval.json"

    approve_candidate(
        candidate_path=candidate,
        output_path=output,
        approval_record_path=approval,
        approved_by="Test Approver",
        confirm_approval=True,
        approved_at=datetime(
            2026,
            9,
            3,
            18,
            0,
            tzinfo=UTC,
        ),
    )

    assert candidate.read_bytes() == before


def test_approval_creates_runtime_loadable_artifact(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(candidate)

    output = tmp_path / "pricing_rules.json"

    approval = tmp_path / "approval.json"

    record = approve_candidate(
        candidate_path=candidate,
        output_path=output,
        approval_record_path=approval,
        approved_by="Test Approver",
        confirm_approval=True,
        approved_at=datetime(
            2026,
            9,
            3,
            18,
            0,
            tzinfo=UTC,
        ),
    )

    approved_payload = json.loads(output.read_text(encoding="utf-8"))

    assert approved_payload["status"] == "APPROVED"

    assert approved_payload["rule_set_id"] == "PRSET-CANDIDATE-TEST"

    assert (
        approved_payload["rules"]
        == json.loads(candidate.read_text(encoding="utf-8"))["rules"]
    )

    loaded = PricingRuleLoader(output).load()

    assert len(loaded) == 1

    assert loaded[0].service_type_id == "STY000001"

    assert record["rule_count"] == 1
    assert record["approved_by"] == "Test Approver"

    assert record["approved_at"] == "2026-09-03T18:00:00Z"


def test_approval_record_contains_hashes(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(candidate)

    output = tmp_path / "pricing_rules.json"

    approval = tmp_path / "approval.json"

    record = approve_candidate(
        candidate_path=candidate,
        output_path=output,
        approval_record_path=approval,
        approved_by="Test Approver",
        confirm_approval=True,
    )

    stored = json.loads(approval.read_text(encoding="utf-8"))

    assert stored == record

    assert len(stored["candidate_sha256"]) == 64

    assert len(stored["approved_artifact_sha256"]) == 64


def test_non_candidate_status_is_rejected(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(
        candidate,
        status="APPROVED",
    )

    with pytest.raises(
        PricingRuntimeApprovalError,
        match="CANDIDATE",
    ):
        approve_candidate(
            candidate_path=candidate,
            output_path=(tmp_path / "pricing_rules.json"),
            approval_record_path=(tmp_path / "approval.json"),
            approved_by="Test Approver",
            confirm_approval=True,
        )


def test_candidate_cannot_be_overwritten(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(candidate)

    with pytest.raises(
        PricingRuntimeApprovalError,
        match="must not overwrite",
    ):
        approve_candidate(
            candidate_path=candidate,
            output_path=candidate,
            approval_record_path=(tmp_path / "approval.json"),
            approved_by="Test Approver",
            confirm_approval=True,
        )


def test_existing_runtime_artifact_is_not_overwritten(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.json"

    write_candidate(candidate)

    output = tmp_path / "pricing_rules.json"

    output.write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(
        PricingRuntimeApprovalError,
        match="already exists",
    ):
        approve_candidate(
            candidate_path=candidate,
            output_path=output,
            approval_record_path=(tmp_path / "approval.json"),
            approved_by="Test Approver",
            confirm_approval=True,
        )

    assert output.read_text(encoding="utf-8") == "existing"

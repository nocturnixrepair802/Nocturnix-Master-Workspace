from __future__ import annotations

import json
from pathlib import Path

from Scripts.export_pricing_runtime_candidate import (
    CANDIDATE_STATUS,
    export_candidate,
)


def test_real_governance_sources_export_expected_candidate(
    tmp_path: Path,
) -> None:
    pricing_dir = Path("Data") / "Pricing"

    candidate_path = tmp_path / "pricing_rules_candidate.json"

    audit_path = tmp_path / "pricing_rules_candidate_audit.json"

    audit = export_candidate(
        workbook_path=(pricing_dir / "Calculation Master_v1.5_Working.xlsx"),
        reconciliation_path=(pricing_dir / "service_type_pricing_reconciliation.csv"),
        governance_path=(pricing_dir / "service_type_governance_decisions_v0.1.csv"),
        output_path=candidate_path,
        audit_path=audit_path,
        rule_set_id="PRSET-TEST-001",
    )

    assert audit.workbook_rows == 101
    assert audit.reconciliation_rows == 101

    assert audit.exact_rows == 70
    assert audit.alias_rows == 3
    assert audit.variant_rows == 13
    assert audit.new_canonical_rows == 11
    assert audit.review_rows == 4

    assert audit.exported_base_rules == 70
    assert audit.exported_variant_rules == 13
    assert audit.exported_total_rules == 83
    assert audit.excluded_rows == 15

    payload = json.loads(candidate_path.read_text(encoding="utf-8"))

    assert payload["status"] == CANDIDATE_STATUS
    assert payload["rule_set_id"] == "PRSET-TEST-001"
    assert len(payload["rules"]) == 83

    identities = {
        (
            rule["service_type_id"],
            rule["variant_key"],
        )
        for rule in payload["rules"]
    }

    assert len(identities) == 83

    assert (
        "STY000061",
        "CORROSION_REMOVAL",
    ) in identities

    assert (
        "STY000006",
        "GLASS_ONLY_REPAIR",
    ) in identities

    assert (
        "STY000055",
        "ADVANCED_DIAGNOSTIC",
    ) in identities

    assert (
        "STY000055",
        "BASE",
    ) in identities

    audit_payload = json.loads(audit_path.read_text(encoding="utf-8"))

    assert len(audit_payload["aliases"]) == 3

    assert len(audit_payload["excluded"]) == 15

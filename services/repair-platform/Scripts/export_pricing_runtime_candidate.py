from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from services.table_loader import TableLoader

SCHEMA_VERSION = "1.0"
CANDIDATE_STATUS = "CANDIDATE"

SERVICE_TABLE = "tblNewServiceTable"
CATEGORY_TABLE = "tblServiceCategoryID"


class PricingRuntimeExportError(RuntimeError):
    """Raised when candidate runtime pricing export cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class ExportAudit:
    workbook_rows: int
    reconciliation_rows: int
    exact_rows: int
    alias_rows: int
    variant_rows: int
    new_canonical_rows: int
    review_rows: int
    exported_base_rules: int
    exported_variant_rules: int
    exported_total_rules: int
    excluded_rows: int


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as file:
        return list(csv.DictReader(file))


def text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def decimal_text(value: Any) -> str:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise PricingRuntimeExportError(
            f"Expected numeric pricing value, got {value!r}."
        ) from exc

    if not result.is_finite():
        raise PricingRuntimeExportError(f"Pricing value must be finite: {value!r}")

    return format(result, "f")


def variant_key(name: str) -> str:
    value = text(name).upper()

    value = re.sub(
        r"[^A-Z0-9]+",
        "_",
        value,
    )

    value = value.strip("_")

    if not value:
        raise PricingRuntimeExportError("Cannot generate a blank pricing variant key.")

    return value


def validate_service_type_id(value: str) -> None:
    if len(value) != 9 or not value.startswith("STY") or not value[3:].isdigit():
        raise PricingRuntimeExportError(f"Invalid canonical Service Type ID: {value!r}")


def validate_service_category_id(value: str) -> None:
    if len(value) != 8 or not value.startswith("SC") or not value[2:].isdigit():
        raise PricingRuntimeExportError(f"Invalid Service Category ID: {value!r}")


def validate_labor_profile_id(value: str) -> None:
    if len(value) != 9 or not value.startswith("LAB") or not value[3:].isdigit():
        raise PricingRuntimeExportError(f"Invalid Labor Profile ID: {value!r}")


def build_rule(
    *,
    service_record: Any,
    category_record: Any,
    service_type_id: str,
    canonical_service_type: str,
    variant_key_value: str = "BASE",
    variant_name: str | None = None,
) -> dict[str, object]:
    service_category_id = text(service_record["Service Category"])

    labor_profile_id = text(service_record["Labor Profile ID"])

    validate_service_type_id(service_type_id)
    validate_service_category_id(service_category_id)
    validate_labor_profile_id(labor_profile_id)

    return {
        "service_type_id": service_type_id,
        "service_type": canonical_service_type,
        "service_category_id": service_category_id,
        "default_labor_hours": decimal_text(service_record["Default Labor Hours"]),
        "labor_profile_id": labor_profile_id,
        "labor_tier": text(service_record["Labor Tier"]),
        "hourly_rate": decimal_text(service_record["Hourly Rate"]),
        "minimum_charge": decimal_text(service_record["Minimum Charge"]),
        "target_margin": decimal_text(category_record["Target Margin"]),
        "minimum_margin": decimal_text(category_record["Minimum Margin"]),
        "overhead_rate": decimal_text(category_record["Overhead"]),
        "warranty_rate": decimal_text(category_record["Warranty"]),
        "risk_rate": decimal_text(category_record["Risk Reserve"]),
        "processing_rate": decimal_text(category_record["Processing"]),
        "rounding_rule": text(category_record["Rounding Rule"]) or "End in .99",
        "variant_key": variant_key_value,
        "variant_name": variant_name,
    }


def export_candidate(
    *,
    workbook_path: Path,
    reconciliation_path: Path,
    governance_path: Path,
    output_path: Path,
    audit_path: Path,
    rule_set_id: str,
) -> ExportAudit:
    loader = TableLoader(workbook_path)

    service_table = loader.load_table(SERVICE_TABLE)

    category_table = loader.load_table(CATEGORY_TABLE)

    reconciliation = read_csv(reconciliation_path)

    governance = read_csv(governance_path)

    if len(service_table) != len(reconciliation):
        raise PricingRuntimeExportError(
            "Workbook service-table row count does not match "
            "pricing reconciliation row count."
        )

    category_by_id: dict[str, Any] = {}

    for _, row in category_table.iterrows():
        category_id = text(row["Service Category ID"])

        if not category_id:
            continue

        if category_id in category_by_id:
            raise PricingRuntimeExportError(
                f"Duplicate service category: {category_id}"
            )

        category_by_id[category_id] = row

    exact_by_name = {
        text(row["Pricing Service Type"]): row
        for row in reconciliation
        if text(row["Match Status"]) == "EXACT"
    }

    governance_by_name = {text(row["Pricing Service Type"]): row for row in governance}

    exact_rows = 0
    alias_rows = 0
    variant_rows = 0
    new_canonical_rows = 0
    review_rows = 0

    rules: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    aliases: list[dict[str, object]] = []

    seen_identities: set[tuple[str, str]] = set()

    def workbook_record(
        reconciliation_row: dict[str, str],
    ) -> Any:
        source_row = int(text(reconciliation_row["Source Row"]))

        index = source_row - 3

        if index < 0 or index >= len(service_table):
            raise PricingRuntimeExportError(
                f"Source Row {source_row} is outside tblNewServiceTable."
            )

        record = service_table.iloc[index]

        workbook_name = text(record["Service Type"])

        pricing_name = text(reconciliation_row["Pricing Service Type"])

        if workbook_name != pricing_name:
            raise PricingRuntimeExportError(
                "Workbook/reconciliation row mismatch: "
                f"{pricing_name!r} != "
                f"{workbook_name!r}"
            )

        return record

    def category_record(
        service_record: Any,
    ) -> Any:
        category_id = text(service_record["Service Category"])

        record = category_by_id.get(category_id)

        if record is None:
            raise PricingRuntimeExportError(
                f"Service category policy not found: {category_id}"
            )

        return record

    def add_rule(
        rule: dict[str, object],
    ) -> None:
        identity = (
            text(rule["service_type_id"]),
            text(rule["variant_key"]).upper() or "BASE",
        )

        if identity in seen_identities:
            raise PricingRuntimeExportError(
                "Duplicate runtime pricing rule identity: "
                f"{identity[0]} / {identity[1]}"
            )

        seen_identities.add(identity)
        rules.append(rule)

    # --------------------------------------------------
    # Exact canonical/base rules
    # --------------------------------------------------

    for row in reconciliation:
        status = text(row["Match Status"])

        if status != "EXACT":
            continue

        exact_rows += 1

        service_type_id = text(row["Canonical Service Type ID"])

        canonical_name = text(row["Canonical Service Type"])

        service_record = workbook_record(row)

        policy = category_record(service_record)

        rule = build_rule(
            service_record=service_record,
            category_record=policy,
            service_type_id=service_type_id,
            canonical_service_type=canonical_name,
            variant_key_value="BASE",
            variant_name=None,
        )

        add_rule(rule)

    # --------------------------------------------------
    # Governance decisions for REVIEW rows
    # --------------------------------------------------

    for row in reconciliation:
        status = text(row["Match Status"])

        if status != "REVIEW":
            continue

        pricing_name = text(row["Pricing Service Type"])

        governance_row = governance_by_name.get(pricing_name)

        if governance_row is None:
            raise PricingRuntimeExportError(
                f"Missing governance decision for {pricing_name!r}."
            )

        decision = text(governance_row["Decision"])

        canonical_target = text(governance_row["Canonical Target"])

        if decision == "ALIAS":
            alias_rows += 1

            target = exact_by_name.get(canonical_target)

            if target is None:
                raise PricingRuntimeExportError(
                    "Alias canonical target does not "
                    f"resolve to an EXACT service: "
                    f"{pricing_name} -> "
                    f"{canonical_target}"
                )

            aliases.append(
                {
                    "source_service_type": (pricing_name),
                    "canonical_target": (canonical_target),
                    "canonical_service_type_id": (
                        text(target["Canonical Service Type ID"])
                    ),
                    "notes": text(governance_row["Notes"]),
                }
            )

            continue

        if decision == "VARIANT":
            variant_rows += 1

            target = exact_by_name.get(canonical_target)

            if target is None:
                raise PricingRuntimeExportError(
                    "Variant canonical target does not "
                    f"resolve to an EXACT service: "
                    f"{pricing_name} -> "
                    f"{canonical_target}"
                )

            service_type_id = text(target["Canonical Service Type ID"])

            canonical_name = text(target["Canonical Service Type"])

            service_record = workbook_record(row)

            policy = category_record(service_record)

            rule = build_rule(
                service_record=service_record,
                category_record=policy,
                service_type_id=service_type_id,
                canonical_service_type=canonical_name,
                variant_key_value=variant_key(pricing_name),
                variant_name=pricing_name,
            )

            add_rule(rule)

            continue

        if decision == "NEW_CANONICAL":
            new_canonical_rows += 1

            excluded.append(
                {
                    "pricing_service_type": (pricing_name),
                    "decision": decision,
                    "reason": (
                        "Requires canonical Service "
                        "Type approval before runtime "
                        "export."
                    ),
                    "notes": text(governance_row["Notes"]),
                }
            )

            continue

        if decision == "REVIEW":
            review_rows += 1

            excluded.append(
                {
                    "pricing_service_type": (pricing_name),
                    "decision": decision,
                    "reason": ("Unresolved governance review."),
                    "notes": text(governance_row["Notes"]),
                }
            )

            continue

        raise PricingRuntimeExportError(
            f"Unsupported governance decision {decision!r} for {pricing_name!r}."
        )

    exported_base_rules = sum(1 for rule in rules if rule["variant_key"] == "BASE")

    exported_variant_rules = len(rules) - exported_base_rules

    audit = ExportAudit(
        workbook_rows=len(service_table),
        reconciliation_rows=len(reconciliation),
        exact_rows=exact_rows,
        alias_rows=alias_rows,
        variant_rows=variant_rows,
        new_canonical_rows=(new_canonical_rows),
        review_rows=review_rows,
        exported_base_rules=(exported_base_rules),
        exported_variant_rules=(exported_variant_rules),
        exported_total_rules=len(rules),
        excluded_rows=len(excluded),
    )

    expected_total = (
        exact_rows + alias_rows + variant_rows + new_canonical_rows + review_rows
    )

    if expected_total != len(reconciliation):
        raise PricingRuntimeExportError(
            "Governance accounting does not cover every reconciliation row."
        )

    if exported_base_rules != exact_rows:
        raise PricingRuntimeExportError(
            "BASE rule count must equal EXACT canonical rule count."
        )

    if exported_variant_rules != variant_rows:
        raise PricingRuntimeExportError(
            "Variant rule count does not match governed VARIANT count."
        )

    candidate_payload = {
        "schema_version": SCHEMA_VERSION,
        "rule_set_id": rule_set_id,
        "status": CANDIDATE_STATUS,
        "rules": rules,
    }

    audit_payload = {
        "rule_set_id": rule_set_id,
        "status": CANDIDATE_STATUS,
        "summary": asdict(audit),
        "aliases": aliases,
        "excluded": excluded,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            candidate_payload,
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )

    audit_path.write_text(
        json.dumps(
            audit_payload,
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return audit


def main() -> None:
    parser = argparse.ArgumentParser(
        description=("Generate a candidate Nocturnix runtime pricing-rule artifact.")
    )

    parser.add_argument(
        "--pricing-dir",
        type=Path,
        default=Path("Data") / "Pricing",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(Path("Data") / "Pricing" / "Runtime Candidate"),
    )

    parser.add_argument(
        "--rule-set-id",
        default="PRSET-CANDIDATE-001",
    )

    args = parser.parse_args()

    pricing_dir: Path = args.pricing_dir

    output_dir: Path = args.output_dir

    audit = export_candidate(
        workbook_path=(pricing_dir / "Calculation Master_v1.5_Working.xlsx"),
        reconciliation_path=(pricing_dir / "service_type_pricing_reconciliation.csv"),
        governance_path=(pricing_dir / "service_type_governance_decisions_v0.1.csv"),
        output_path=(output_dir / "pricing_rules_candidate.json"),
        audit_path=(output_dir / "pricing_rules_candidate_audit.json"),
        rule_set_id=args.rule_set_id,
    )

    print()
    print("=" * 72)
    print("Nocturnix Pricing Runtime Candidate Export")
    print("=" * 72)

    print(
        "Workbook rows:",
        audit.workbook_rows,
    )

    print(
        "EXACT:",
        audit.exact_rows,
    )

    print(
        "ALIAS:",
        audit.alias_rows,
    )

    print(
        "VARIANT:",
        audit.variant_rows,
    )

    print(
        "NEW_CANONICAL:",
        audit.new_canonical_rows,
    )

    print(
        "REVIEW:",
        audit.review_rows,
    )

    print()

    print(
        "BASE rules exported:",
        audit.exported_base_rules,
    )

    print(
        "Variant rules exported:",
        audit.exported_variant_rules,
    )

    print(
        "Total runtime rules:",
        audit.exported_total_rules,
    )

    print(
        "Excluded rows:",
        audit.excluded_rows,
    )

    print()

    print(
        "Candidate:",
        (output_dir / "pricing_rules_candidate.json"),
    )

    print(
        "Audit:",
        (output_dir / "pricing_rules_candidate_audit.json"),
    )

    print()
    print("NOTE: Candidate status is not runtime-approved.")


if __name__ == "__main__":
    main()

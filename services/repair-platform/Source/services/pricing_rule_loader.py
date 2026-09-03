from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from models.service_pricing import ServicePricingRule

SUPPORTED_SCHEMA_VERSION = "1.0"
APPROVED_STATUS = "APPROVED"


class PricingRuleLoadError(RuntimeError):
    """Base error for pricing-rule runtime artifact loading."""


class PricingRuleFileNotFoundError(PricingRuleLoadError):
    """Raised when the configured pricing-rule artifact does not exist."""


class PricingRuleFormatError(PricingRuleLoadError):
    """Raised when the runtime artifact is structurally invalid."""


class PricingRuleApprovalError(PricingRuleLoadError):
    """Raised when the runtime artifact is not explicitly approved."""


class PricingRuleLoader:
    """
    Load an explicitly approved Nocturnix pricing-rule JSON artifact.

    This loader:

    - performs no workbook reads;
    - performs no governance approval;
    - requires the artifact itself to declare APPROVED status;
    - validates the supported schema version;
    - converts governed numeric fields to Decimal;
    - returns immutable ServicePricingRule models.

    Approval/export of the runtime artifact is a separate governance
    process outside this loader.
    """

    def __init__(
        self,
        artifact_path: str | Path,
    ) -> None:
        self.artifact_path = Path(artifact_path)

    def load(self) -> tuple[ServicePricingRule, ...]:
        payload = self._read_payload()

        self._validate_metadata(payload)

        raw_rules = payload.get("rules")

        if not isinstance(raw_rules, list):
            raise PricingRuleFormatError(
                "Pricing rule artifact field 'rules' must be a list."
            )

        rules: list[ServicePricingRule] = []
        seen_service_type_ids: set[str] = set()

        for index, raw_rule in enumerate(
            raw_rules,
            start=1,
        ):
            if not isinstance(raw_rule, dict):
                raise PricingRuleFormatError(
                    f"Pricing rule #{index} must be an object."
                )

            rule = self._parse_rule(
                raw_rule,
                index=index,
            )

            if rule.service_type_id in seen_service_type_ids:
                raise PricingRuleFormatError(
                    "Duplicate pricing rule for Service Type: "
                    f"{rule.service_type_id}"
                )

            seen_service_type_ids.add(rule.service_type_id)

            rules.append(rule)

        return tuple(rules)

    def _read_payload(self) -> dict[str, Any]:
        if not self.artifact_path.exists():
            raise PricingRuleFileNotFoundError(
                f"Pricing rule artifact not found: " f"{self.artifact_path}"
            )

        if not self.artifact_path.is_file():
            raise PricingRuleFormatError(
                "Pricing rule artifact path must point to a file."
            )

        try:
            text = self.artifact_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PricingRuleLoadError(
                "Pricing rule artifact could not be read."
            ) from exc

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise PricingRuleFormatError(
                "Pricing rule artifact is not valid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise PricingRuleFormatError(
                "Pricing rule artifact root must be an object."
            )

        return payload

    @staticmethod
    def _validate_metadata(
        payload: dict[str, Any],
    ) -> None:
        schema_version = str(payload.get("schema_version") or "").strip()

        if schema_version != SUPPORTED_SCHEMA_VERSION:
            raise PricingRuleFormatError(
                "Unsupported pricing rule schema_version: "
                f"{schema_version or '<blank>'}"
            )

        rule_set_id = str(payload.get("rule_set_id") or "").strip()

        if not rule_set_id:
            raise PricingRuleFormatError("Pricing rule artifact requires rule_set_id.")

        status = str(payload.get("status") or "").strip().upper()

        if status != APPROVED_STATUS:
            raise PricingRuleApprovalError(
                "Pricing rule artifact must have " "status APPROVED."
            )

    def _parse_rule(
        self,
        raw_rule: dict[str, Any],
        *,
        index: int,
    ) -> ServicePricingRule:
        service_type_id = self._required_text(
            raw_rule,
            "service_type_id",
            index=index,
        )

        if (
            len(service_type_id) != 9
            or not service_type_id.startswith("STY")
            or not service_type_id[3:].isdigit()
        ):
            raise PricingRuleFormatError(
                f"Pricing rule #{index} has invalid "
                "service_type_id. Expected STY######."
            )

        service_category_id = self._required_text(
            raw_rule,
            "service_category_id",
            index=index,
        )

        if (
            len(service_category_id) != 8
            or not service_category_id.startswith("SC")
            or not service_category_id[2:].isdigit()
        ):
            raise PricingRuleFormatError(
                f"Pricing rule #{index} has invalid "
                "service_category_id. Expected SC######."
            )

        labor_profile_id = self._required_text(
            raw_rule,
            "labor_profile_id",
            index=index,
        )

        if (
            len(labor_profile_id) != 9
            or not labor_profile_id.startswith("LAB")
            or not labor_profile_id[3:].isdigit()
        ):
            raise PricingRuleFormatError(
                f"Pricing rule #{index} has invalid "
                "labor_profile_id. Expected LAB######."
            )

        return ServicePricingRule(
            service_type_id=service_type_id,
            service_type=self._required_text(
                raw_rule,
                "service_type",
                index=index,
            ),
            service_category_id=service_category_id,
            default_labor_hours=self._decimal(
                raw_rule,
                "default_labor_hours",
                index=index,
            ),
            labor_profile_id=labor_profile_id,
            labor_tier=self._required_text(
                raw_rule,
                "labor_tier",
                index=index,
            ),
            hourly_rate=self._decimal(
                raw_rule,
                "hourly_rate",
                index=index,
            ),
            minimum_charge=self._decimal(
                raw_rule,
                "minimum_charge",
                index=index,
            ),
            target_margin=self._decimal(
                raw_rule,
                "target_margin",
                index=index,
            ),
            minimum_margin=self._decimal(
                raw_rule,
                "minimum_margin",
                index=index,
            ),
            overhead_rate=self._decimal(
                raw_rule,
                "overhead_rate",
                index=index,
            ),
            warranty_rate=self._decimal(
                raw_rule,
                "warranty_rate",
                index=index,
            ),
            risk_rate=self._decimal(
                raw_rule,
                "risk_rate",
                index=index,
            ),
            processing_rate=self._decimal(
                raw_rule,
                "processing_rate",
                index=index,
            ),
            rounding_rule=str(
                raw_rule.get(
                    "rounding_rule",
                    "End in .99",
                )
                or "End in .99"
            ).strip(),
        )

    @staticmethod
    def _required_text(
        raw_rule: dict[str, Any],
        field: str,
        *,
        index: int,
    ) -> str:
        value = str(raw_rule.get(field) or "").strip()

        if not value:
            raise PricingRuleFormatError(
                f"Pricing rule #{index} requires " f"field '{field}'."
            )

        return value

    @staticmethod
    def _decimal(
        raw_rule: dict[str, Any],
        field: str,
        *,
        index: int,
    ) -> Decimal:
        value = raw_rule.get(field)

        if value is None or value == "":
            raise PricingRuleFormatError(
                f"Pricing rule #{index} requires " f"field '{field}'."
            )

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise PricingRuleFormatError(
                f"Pricing rule #{index} field " f"'{field}' must be numeric."
            ) from exc

        if not decimal_value.is_finite():
            raise PricingRuleFormatError(
                f"Pricing rule #{index} field " f"'{field}' must be finite."
            )

        return decimal_value

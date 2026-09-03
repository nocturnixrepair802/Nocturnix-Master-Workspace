from __future__ import annotations

from collections.abc import Iterable

from models.service_pricing import ServicePricingRule


class PricingRuleNotFoundError(LookupError):
    """Raised when no pricing rule exists for a Service Type."""


class DuplicatePricingRuleError(ValueError):
    """Raised when duplicate Service Type rules are supplied."""


class PricingRuleProvider:
    """
    Read-only runtime provider for explicitly supplied pricing rules.

    This provider intentionally performs no workbook, database, or API I/O.

    Rules supplied to this provider must already have passed the
    appropriate Nocturnix governance/review process for the calling
    context.

    This class does not promote review-local STY identifiers or labor
    mappings into canonical authority.
    """

    def __init__(
        self,
        rules: Iterable[ServicePricingRule] = (),
    ) -> None:
        self._rules: dict[str, ServicePricingRule] = {}

        for rule in rules:
            service_type_id = str(rule.service_type_id).strip()

            if service_type_id in self._rules:
                raise DuplicatePricingRuleError(
                    "Duplicate pricing rule for Service Type: " f"{service_type_id}"
                )

            self._rules[service_type_id] = rule

    def get(
        self,
        service_type_id: str,
    ) -> ServicePricingRule:
        resolved_id = str(service_type_id).strip()

        rule = self._rules.get(resolved_id)

        if rule is None:
            raise PricingRuleNotFoundError(f"Pricing rule not found: {resolved_id}")

        return rule

    def get_optional(
        self,
        service_type_id: str,
    ) -> ServicePricingRule | None:
        resolved_id = str(service_type_id).strip()

        return self._rules.get(resolved_id)

    def all(
        self,
    ) -> tuple[ServicePricingRule, ...]:
        return tuple(self._rules.values())

    def count(
        self,
    ) -> int:
        return len(self._rules)

    def contains(
        self,
        service_type_id: str,
    ) -> bool:
        resolved_id = str(service_type_id).strip()

        return resolved_id in self._rules

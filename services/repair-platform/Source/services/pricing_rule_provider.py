from __future__ import annotations

from collections.abc import Iterable

from models.service_pricing import ServicePricingRule

BASE_VARIANT_KEY = "BASE"


class PricingRuleNotFoundError(LookupError):
    """Raised when no pricing rule exists for a Service Type variant."""


class DuplicatePricingRuleError(ValueError):
    """Raised when duplicate Service Type variant rules are supplied."""


class PricingRuleProvider:
    """
    Read-only runtime provider for explicitly supplied pricing rules.

    Runtime rule identity is:

        (service_type_id, variant_key)

    Base canonical rules use:

        variant_key = "BASE"

    Pricing variants may share the same canonical Service Type ID while
    preserving distinct labor and pricing policy.

    This provider intentionally performs no workbook, database, or API I/O.

    Rules supplied to this provider must already have passed the
    appropriate Nocturnix governance/review process for the calling
    context.

    This class does not promote review-local STY identifiers, variants,
    or labor mappings into canonical authority.
    """

    def __init__(
        self,
        rules: Iterable[ServicePricingRule] = (),
    ) -> None:
        self._rules: dict[
            tuple[str, str],
            ServicePricingRule,
        ] = {}

        for rule in rules:
            service_type_id = self._normalize_service_type_id(rule.service_type_id)

            variant_key = self._normalize_variant_key(rule.variant_key)

            identity = (
                service_type_id,
                variant_key,
            )

            if identity in self._rules:
                raise DuplicatePricingRuleError(
                    "Duplicate pricing rule for "
                    f"Service Type {service_type_id} "
                    f"variant {variant_key}"
                )

            self._rules[identity] = rule

    def get(
        self,
        service_type_id: str,
        variant_key: str = BASE_VARIANT_KEY,
    ) -> ServicePricingRule:
        resolved_id = self._normalize_service_type_id(service_type_id)
        resolved_variant = self._normalize_variant_key(variant_key)

        rule = self._rules.get(
            (
                resolved_id,
                resolved_variant,
            )
        )

        if rule is None:
            raise PricingRuleNotFoundError(
                "Pricing rule not found: "
                f"{resolved_id} "
                f"variant {resolved_variant}"
            )

        return rule

    def get_optional(
        self,
        service_type_id: str,
        variant_key: str = BASE_VARIANT_KEY,
    ) -> ServicePricingRule | None:
        resolved_id = self._normalize_service_type_id(service_type_id)
        resolved_variant = self._normalize_variant_key(variant_key)

        return self._rules.get(
            (
                resolved_id,
                resolved_variant,
            )
        )

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
        variant_key: str = BASE_VARIANT_KEY,
    ) -> bool:
        resolved_id = self._normalize_service_type_id(service_type_id)
        resolved_variant = self._normalize_variant_key(variant_key)

        return (
            resolved_id,
            resolved_variant,
        ) in self._rules

    @staticmethod
    def _normalize_service_type_id(
        service_type_id: str,
    ) -> str:
        return str(service_type_id).strip()

    @staticmethod
    def _normalize_variant_key(
        variant_key: str,
    ) -> str:
        value = str(variant_key).strip().upper()

        if not value:
            return BASE_VARIANT_KEY

        return value

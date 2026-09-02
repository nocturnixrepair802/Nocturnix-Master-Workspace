from __future__ import annotations

from decimal import Decimal, ROUND_CEILING
from typing import Any

from exceptions.pricing_exception import PricingException


class PricingEngine:
    """
    Nocturnix service pricing calculation engine.

    This engine performs pricing calculations only.

    Provider responsibilities remain separate:

    - Mobile Sentrix supplies product/SKU pricing and availability.
    - Nocturnix supplies labor rules, pricing policy, market data,
      and final pricing decisions.
    - The pricing engine performs no provider or database I/O.
    """

    MONEY = Decimal("0.01")

    def __init__(self, database: Any | None = None) -> None:
        """
        Initialize the pricing calculation engine.

        ``database`` is accepted temporarily for compatibility with
        legacy QuoteEngine and RepairManager construction. The governed
        pricing engine performs no database I/O and does not retain or
        use the supplied value.
        """
        del database

    def calculate(
        self,
        *,
        part_cost: float | Decimal,
        default_labor_hours: float | Decimal,
        hourly_rate: float | Decimal,
        minimum_charge: float | Decimal,
        shipping: float | Decimal = 0,
        consumables: float | Decimal = 5,
        overhead_rate: float | Decimal = 0,
        warranty_rate: float | Decimal = 0,
        risk_rate: float | Decimal = 0,
        processing_rate: float | Decimal = 0,
        target_margin: float | Decimal = 0,
        minimum_margin: float | Decimal = 0,
    ) -> dict[str, Any]:
        """
        Calculate a complete Nocturnix service pricing preview.

        Percentage/rate values are decimal fractions.

        Example:
            12% -> Decimal("0.12")
            30% -> Decimal("0.30")
        """

        part_cost_value = self._money(part_cost)
        labor_hours_value = self._decimal(default_labor_hours)
        hourly_rate_value = self._money(hourly_rate)
        minimum_charge_value = self._money(minimum_charge)
        shipping_value = self._money(shipping)
        consumables_value = self._money(consumables)

        overhead_rate_value = self._rate(
            overhead_rate,
            "overhead_rate",
        )
        warranty_rate_value = self._rate(
            warranty_rate,
            "warranty_rate",
        )
        risk_rate_value = self._rate(
            risk_rate,
            "risk_rate",
        )
        processing_rate_value = self._rate(
            processing_rate,
            "processing_rate",
        )
        target_margin_value = self._rate(
            target_margin,
            "target_margin",
        )
        minimum_margin_value = self._rate(
            minimum_margin,
            "minimum_margin",
        )

        if target_margin_value >= Decimal("1"):
            raise PricingException("target_margin must be less than 1.00.")

        if minimum_margin_value > target_margin_value:
            raise PricingException("minimum_margin cannot exceed target_margin.")

        calculated_labor_cost = self._money(labor_hours_value * hourly_rate_value)

        billable_labor_cost = max(
            calculated_labor_cost,
            minimum_charge_value,
        )

        base_direct_cost = self._money(
            part_cost_value + billable_labor_cost + shipping_value + consumables_value
        )

        overhead_reserve = self._money(base_direct_cost * overhead_rate_value)

        warranty_reserve = self._money(base_direct_cost * warranty_rate_value)

        risk_reserve = self._money(base_direct_cost * risk_rate_value)

        processing_reserve = self._money(base_direct_cost * processing_rate_value)

        total_internal_cost = self._money(
            base_direct_cost
            + overhead_reserve
            + warranty_reserve
            + risk_reserve
            + processing_reserve
        )

        raw_retail_price = self._money(
            total_internal_cost / (Decimal("1") - target_margin_value)
        )

        recommended_retail_price = self._round_to_99(raw_retail_price)

        gross_profit = self._money(recommended_retail_price - total_internal_cost)

        if recommended_retail_price == 0:
            gross_margin = Decimal("0")
        else:
            gross_margin = (gross_profit / recommended_retail_price).quantize(
                Decimal("0.0001")
            )

        pricing_status = self._pricing_status(
            gross_margin=gross_margin,
            target_margin=target_margin_value,
            minimum_margin=minimum_margin_value,
        )

        return {
            "part_cost": part_cost_value,
            "default_labor_hours": labor_hours_value,
            "hourly_rate": hourly_rate_value,
            "minimum_charge": minimum_charge_value,
            "calculated_labor_cost": calculated_labor_cost,
            "billable_labor_cost": billable_labor_cost,
            "shipping": shipping_value,
            "consumables": consumables_value,
            "base_direct_cost": base_direct_cost,
            "overhead_rate": overhead_rate_value,
            "overhead_reserve": overhead_reserve,
            "warranty_rate": warranty_rate_value,
            "warranty_reserve": warranty_reserve,
            "risk_rate": risk_rate_value,
            "risk_reserve": risk_reserve,
            "processing_rate": processing_rate_value,
            "processing_reserve": processing_reserve,
            "total_internal_cost": total_internal_cost,
            "target_margin": target_margin_value,
            "minimum_margin": minimum_margin_value,
            "raw_retail_price": raw_retail_price,
            "recommended_retail_price": recommended_retail_price,
            "gross_profit": gross_profit,
            "gross_margin": gross_margin,
            "pricing_status": pricing_status,
        }

    @classmethod
    def _decimal(
        cls,
        value: float | Decimal | int | str,
    ) -> Decimal:
        try:
            result = Decimal(str(value))
        except Exception as exc:
            raise PricingException(f"Invalid numeric pricing value: {value!r}") from exc

        if result < 0:
            raise PricingException("Pricing values cannot be negative.")

        return result

    @classmethod
    def _money(
        cls,
        value: float | Decimal | int | str,
    ) -> Decimal:
        return cls._decimal(value).quantize(cls.MONEY)

    @classmethod
    def _rate(
        cls,
        value: float | Decimal | int | str,
        field_name: str,
    ) -> Decimal:
        result = cls._decimal(value)

        if result > Decimal("1"):
            raise PricingException(
                f"{field_name} must be expressed as a decimal "
                "fraction between 0 and 1."
            )

        return result

    @classmethod
    def _round_to_99(
        cls,
        raw_price: Decimal,
    ) -> Decimal:
        """
        Round upward to a retail price ending in .99.

        Examples:
            143.12 -> 143.99
            143.99 -> 143.99
            144.00 -> 144.99

        The returned price will never be below raw_price.
        """

        if raw_price <= 0:
            return Decimal("0.00")

        whole_dollars = raw_price.to_integral_value(rounding=ROUND_CEILING)

        candidate = whole_dollars - Decimal("0.01")

        if candidate < raw_price:
            candidate += Decimal("1.00")

        return candidate.quantize(cls.MONEY)

    @staticmethod
    def _pricing_status(
        *,
        gross_margin: Decimal,
        target_margin: Decimal,
        minimum_margin: Decimal,
    ) -> str:
        if gross_margin >= target_margin:
            return "READY"

        if gross_margin >= minimum_margin:
            return "MARGIN REVIEW"

        return "BELOW MINIMUM"

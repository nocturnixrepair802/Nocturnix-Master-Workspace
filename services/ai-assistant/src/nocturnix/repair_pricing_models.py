"""Domain models for deterministic repair pricing calculations."""

from pydantic import BaseModel, ConfigDict, Field


class RepairPricingRequest(BaseModel):
    """Validated inputs required to calculate a repair price."""

    model_config = ConfigDict(extra="forbid")

    parts_cost_cents: int = Field(
        default=0,
        ge=0,
        description="Total internal parts cost in cents.",
    )
    labor_cost_cents: int = Field(
        default=0,
        ge=0,
        description="Total internal labor cost in cents.",
    )
    processing_fee_cents: int = Field(
        default=0,
        ge=0,
        description="Processing fee charged to the customer in cents.",
    )
    overhead_cents: int = Field(
        default=0,
        ge=0,
        description="Allocated business overhead in cents.",
    )
    markup_basis_points: int = Field(
        default=0,
        ge=0,
        description=(
            "Markup applied to parts, labor, and overhead. "
            "One hundred basis points equals one percent."
        ),
    )
    tax_rate_basis_points: int = Field(
        default=0,
        ge=0,
        le=10_000,
        description=("Tax rate in basis points. For example, 725 represents 7.25 percent."),
    )


class RepairPolicyPricingRequest(BaseModel):
    """Business inputs priced using the owner's default policies."""

    model_config = ConfigDict(extra="forbid")

    parts_cost_cents: int = Field(
        default=0,
        ge=0,
        description="Total internal parts cost in cents.",
    )
    labor_minutes: int = Field(
        default=0,
        ge=0,
        description="Estimated labor time in whole minutes.",
    )


class RepairPricingResponse(BaseModel):
    """Complete calculated pricing breakdown."""

    model_config = ConfigDict(extra="forbid")

    parts_cost_cents: int
    labor_cost_cents: int
    processing_fee_cents: int
    overhead_cents: int

    internal_cost_cents: int
    markup_amount_cents: int
    subtotal_before_tax_cents: int
    taxable_subtotal_cents: int
    tax_amount_cents: int
    total_price_cents: int

    gross_profit_cents: int
    gross_margin_basis_points: int

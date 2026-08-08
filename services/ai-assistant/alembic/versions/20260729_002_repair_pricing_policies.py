"""add repair pricing policies

Revision ID: 20260729_002
Revises: d289ba2520d6
Create Date: 2026-07-29 18:37:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260729_002"
down_revision: str | Sequence[str] | None = "d289ba2520d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create repair pricing policy persistence."""

    op.create_table(
        "repair_pricing_policies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "labor_rate_cents_per_hour",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "processing_fee_cents",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "overhead_basis_points",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "markup_basis_points",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "effective_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "labor_rate_cents_per_hour >= 0",
            name="ck_repair_pricing_policy_labor_rate_nonnegative",
        ),
        sa.CheckConstraint(
            "processing_fee_cents >= 0",
            name="ck_repair_pricing_policy_processing_fee_nonnegative",
        ),
        sa.CheckConstraint(
            "overhead_basis_points >= 0",
            name="ck_repair_pricing_policy_overhead_nonnegative",
        ),
        sa.CheckConstraint(
            "markup_basis_points >= 0",
            name="ck_repair_pricing_policy_markup_nonnegative",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_user_id",
            "name",
            name="uq_repair_pricing_policy_name",
        ),
    )

    op.create_index(
        op.f("ix_repair_pricing_policies_effective_at"),
        "repair_pricing_policies",
        ["effective_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_repair_pricing_policies_owner_user_id"),
        "repair_pricing_policies",
        ["owner_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove repair pricing policy persistence."""

    op.drop_index(
        op.f("ix_repair_pricing_policies_owner_user_id"),
        table_name="repair_pricing_policies",
    )

    op.drop_index(
        op.f("ix_repair_pricing_policies_effective_at"),
        table_name="repair_pricing_policies",
    )

    op.drop_table("repair_pricing_policies")

"""add repair tax policies

Revision ID: d289ba2520d6
Revises: 20260729_001
Create Date: 2026-07-29 14:57:36.548504
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d289ba2520d6"
down_revision: str | Sequence[str] | None = "20260729_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create repair tax policy persistence."""

    op.create_table(
        "repair_tax_policies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("jurisdiction", sa.String(length=120), nullable=True),
        sa.Column("tax_rate_basis_points", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_user_id",
            "name",
            name="uq_repair_tax_policy_name",
        ),
    )

    op.create_index(
        op.f("ix_repair_tax_policies_effective_at"),
        "repair_tax_policies",
        ["effective_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repair_tax_policies_owner_user_id"),
        "repair_tax_policies",
        ["owner_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove repair tax policy persistence."""

    op.drop_index(
        op.f("ix_repair_tax_policies_owner_user_id"),
        table_name="repair_tax_policies",
    )
    op.drop_index(
        op.f("ix_repair_tax_policies_effective_at"),
        table_name="repair_tax_policies",
    )
    op.drop_table("repair_tax_policies")

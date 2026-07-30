"""add repair service catalog

Revision ID: 15232780e259
Revises: 20260729_002
Create Date: 2026-07-29 22:50:13.277894

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15232780e259"
down_revision: str | Sequence[str] | None = "20260729_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "repair_services",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_labor_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("taxable", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "default_labor_minutes >= 0",
            name="ck_repair_services_default_labor_minutes_nonnegative",
        ),
        sa.CheckConstraint(
            (
                "estimated_duration_minutes IS NULL "
                "OR estimated_duration_minutes >= 0"
            ),
            name="ck_repair_services_estimated_duration_minutes_nonnegative",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_repair_services_category"),
        "repair_services",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repair_services_is_active"),
        "repair_services",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_repair_services_owner_active",
        "repair_services",
        ["owner_user_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_repair_services_owner_category",
        "repair_services",
        ["owner_user_id", "category"],
        unique=False,
    )
    op.create_index(
        "ix_repair_services_owner_name",
        "repair_services",
        ["owner_user_id", "name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repair_services_owner_user_id"),
        "repair_services",
        ["owner_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_repair_services_owner_user_id"),
        table_name="repair_services",
    )
    op.drop_index(
        "ix_repair_services_owner_name",
        table_name="repair_services",
    )
    op.drop_index(
        "ix_repair_services_owner_category",
        table_name="repair_services",
    )
    op.drop_index(
        "ix_repair_services_owner_active",
        table_name="repair_services",
    )
    op.drop_index(
        op.f("ix_repair_services_is_active"),
        table_name="repair_services",
    )
    op.drop_index(
        op.f("ix_repair_services_category"),
        table_name="repair_services",
    )
    op.drop_table("repair_services")

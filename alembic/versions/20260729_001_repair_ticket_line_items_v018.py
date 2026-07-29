"""add repair ticket line items for v0.1.8

Revision ID: 20260729_001
Revises: 20260724_004
Create Date: 2026-07-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_001"
down_revision: str | None = "20260724_004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repair_ticket_line_items",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("repair_ticket_id", sa.String(64), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("line_type", sa.String(30), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("unit_cost_cents", sa.Integer(), nullable=True),
        sa.Column("discount_cents", sa.Integer(), nullable=False),
        sa.Column("line_total_cents", sa.Integer(), nullable=False),
        sa.Column("taxable", sa.Boolean(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["repair_ticket_id"],
            ["repair_tickets.id"],
        ),
        sa.UniqueConstraint(
            "repair_ticket_id",
            "line_number",
            name="uq_repair_ticket_line_items_ticket_line",
        ),
    )

    op.create_index(
        "ix_repair_ticket_line_items_owner_user_id",
        "repair_ticket_line_items",
        ["owner_user_id"],
    )
    op.create_index(
        "ix_repair_ticket_line_items_repair_ticket_id",
        "repair_ticket_line_items",
        ["repair_ticket_id"],
    )
    op.create_index(
        "ix_repair_ticket_line_items_line_type",
        "repair_ticket_line_items",
        ["line_type"],
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.8."
    )

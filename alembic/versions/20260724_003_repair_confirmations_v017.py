"""persist repair AI confirmations for v0.1.7

Revision ID: 20260724_003
Revises: 20260724_002
Create Date: 2026-07-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_003"
down_revision: str | None = "20260724_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repair_confirmations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("previous_response_id", sa.String(200), nullable=False),
        sa.Column("tool_name", sa.String(120), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("action_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_repair_confirmations_owner_user_id",
        "repair_confirmations",
        ["owner_user_id"],
    )
    op.create_index(
        "ix_repair_confirmations_expires_at",
        "repair_confirmations",
        ["expires_at"],
    )
    op.create_index(
        "ix_repair_confirmations_consumed_at",
        "repair_confirmations",
        ["consumed_at"],
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.7."
    )

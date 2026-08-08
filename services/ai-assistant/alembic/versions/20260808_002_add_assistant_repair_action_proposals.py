"""add assistant repair action proposals

Revision ID: 20260808_002
Revises: 20260808_001
Create Date: 2026-08-08 04:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260808_002"
down_revision: str | None = "20260808_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_repair_action_proposals",
        sa.Column(
            "id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "owner_user_id",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "action_type",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "ticket_id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "note_type",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "body",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "customer_visible",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "applied_by_user_id",
            sa.String(length=120),
            nullable=True,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_assistant_repair_action_proposals_owner_user_id"),
        "assistant_repair_action_proposals",
        ["owner_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_assistant_repair_action_proposals_action_type"),
        "assistant_repair_action_proposals",
        ["action_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_assistant_repair_action_proposals_status"),
        "assistant_repair_action_proposals",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_assistant_repair_action_proposals_ticket_id"),
        "assistant_repair_action_proposals",
        ["ticket_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_assistant_repair_action_proposals_ticket_id"),
        table_name=("assistant_repair_action_proposals"),
    )

    op.drop_index(
        op.f("ix_assistant_repair_action_proposals_status"),
        table_name=("assistant_repair_action_proposals"),
    )

    op.drop_index(
        op.f("ix_assistant_repair_action_proposals_action_type"),
        table_name=("assistant_repair_action_proposals"),
    )

    op.drop_index(
        op.f("ix_assistant_repair_action_proposals_owner_user_id"),
        table_name=("assistant_repair_action_proposals"),
    )

    op.drop_table("assistant_repair_action_proposals")

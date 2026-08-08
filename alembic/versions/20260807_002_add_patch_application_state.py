"""add patch application state

Revision ID: 20260807_002
Revises: 20260807_001
Create Date: 2026-08-07 23:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260807_002"
down_revision: str | None = "20260807_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assistant_patch_proposals",
        sa.Column(
            "status",
            sa.String(length=40),
            nullable=False,
            server_default="pending",
        ),
    )

    op.add_column(
        "assistant_patch_proposals",
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "assistant_patch_proposals",
        sa.Column(
            "applied_by_user_id",
            sa.String(length=120),
            nullable=True,
        ),
    )

    op.add_column(
        "assistant_patch_proposals",
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_assistant_patch_proposals_status"),
        "assistant_patch_proposals",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_assistant_patch_proposals_applied_by_user_id"),
        "assistant_patch_proposals",
        ["applied_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_assistant_patch_proposals_applied_by_user_id"),
        table_name="assistant_patch_proposals",
    )

    op.drop_index(
        op.f("ix_assistant_patch_proposals_status"),
        table_name="assistant_patch_proposals",
    )

    op.drop_column(
        "assistant_patch_proposals",
        "failure_reason",
    )

    op.drop_column(
        "assistant_patch_proposals",
        "applied_by_user_id",
    )

    op.drop_column(
        "assistant_patch_proposals",
        "applied_at",
    )

    op.drop_column(
        "assistant_patch_proposals",
        "status",
    )

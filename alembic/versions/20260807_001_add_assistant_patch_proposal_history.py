"""add assistant patch proposal history

Revision ID: 20260807_001
Revises: 4c7d288f5576
Create Date: 2026-08-07 19:55:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260807_001"
down_revision: str | None = "4c7d288f5576"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_patch_proposals",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("conversation_id", sa.String(), nullable=True),
        sa.Column("repository_root", sa.String(length=500), nullable=False),
        sa.Column("target_file", sa.String(length=500), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("unified_diff", sa.Text(), nullable=False),
        sa.Column("original_sha256", sa.String(length=64), nullable=False),
        sa.Column("proposed_sha256", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["assistant_tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_assistant_patch_proposals_owner_user_id"),
        "assistant_patch_proposals",
        ["owner_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_assistant_patch_proposals_task_id"),
        "assistant_patch_proposals",
        ["task_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_assistant_patch_proposals_conversation_id"),
        "assistant_patch_proposals",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_assistant_patch_proposals_conversation_id"),
        table_name="assistant_patch_proposals",
    )

    op.drop_index(
        op.f("ix_assistant_patch_proposals_task_id"),
        table_name="assistant_patch_proposals",
    )

    op.drop_index(
        op.f("ix_assistant_patch_proposals_owner_user_id"),
        table_name="assistant_patch_proposals",
    )

    op.drop_table("assistant_patch_proposals")

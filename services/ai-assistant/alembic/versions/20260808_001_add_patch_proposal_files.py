"""add patch proposal file changes

Revision ID: 20260808_001
Revises: 20260807_002
Create Date: 2026-08-08 01:50:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260808_001"
down_revision: str | None = "20260807_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_patch_proposal_files",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "proposal_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "ordinal",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "path",
            sa.String(length=1000),
            nullable=False,
        ),
        sa.Column(
            "unified_diff",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "original_sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "proposed_sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["proposal_id"],
            ["assistant_patch_proposals.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "proposal_id",
            "ordinal",
            name="uq_patch_proposal_file_ordinal",
        ),
        sa.UniqueConstraint(
            "proposal_id",
            "path",
            name="uq_patch_proposal_file_path",
        ),
    )

    op.create_index(
        op.f("ix_assistant_patch_proposal_files_proposal_id"),
        "assistant_patch_proposal_files",
        ["proposal_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_assistant_patch_proposal_files_proposal_id"),
        table_name="assistant_patch_proposal_files",
    )

    op.drop_table("assistant_patch_proposal_files")

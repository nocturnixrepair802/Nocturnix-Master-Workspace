"""add assistant task and result tables

Revision ID: 4c7d288f5576
Revises: 15232780e259
Create Date: 2026-08-05 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4c7d288f5576"
down_revision: str | None = "15232780e259"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("conversation_id", sa.String(), nullable=True),
        sa.Column("task_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assistant_tasks_conversation_id"),
        "assistant_tasks",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_tasks_owner_user_id"),
        "assistant_tasks",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(op.f("ix_assistant_tasks_status"), "assistant_tasks", ["status"], unique=False)
    op.create_index(
        op.f("ix_assistant_tasks_task_type"),
        "assistant_tasks",
        ["task_type"],
        unique=False,
    )

    op.create_table(
        "assistant_results",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=120), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("result_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("media_type", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["assistant_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assistant_results_owner_user_id"),
        "assistant_results",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_results_result_type"),
        "assistant_results",
        ["result_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_results_task_id"),
        "assistant_results",
        ["task_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_assistant_results_task_id"), table_name="assistant_results")
    op.drop_index(op.f("ix_assistant_results_result_type"), table_name="assistant_results")
    op.drop_index(op.f("ix_assistant_results_owner_user_id"), table_name="assistant_results")
    op.drop_table("assistant_results")
    op.drop_index(op.f("ix_assistant_tasks_task_type"), table_name="assistant_tasks")
    op.drop_index(op.f("ix_assistant_tasks_status"), table_name="assistant_tasks")
    op.drop_index(op.f("ix_assistant_tasks_owner_user_id"), table_name="assistant_tasks")
    op.drop_index(op.f("ix_assistant_tasks_conversation_id"), table_name="assistant_tasks")
    op.drop_table("assistant_tasks")

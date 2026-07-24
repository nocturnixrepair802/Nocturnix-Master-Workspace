"""memory planning and autonomous task engine for v0.1.6

Revision ID: 20260724_002
Revises: 20260724_001
Create Date: 2026-07-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_002"
down_revision: str | None = "20260724_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("visibility", sa.String(40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("related_memory_ids", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("ai_generated", sa.Boolean(), nullable=False),
        sa.Column("manual", sa.Boolean(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("search_vector", sa.Text(), nullable=False),
    )
    for c in [
        "owner_user_id",
        "category",
        "expires_at",
        "archived",
        "deleted",
        "pinned",
        "favorite",
    ]:
        op.create_index(f"ix_memories_{c}", "memories", [c])
    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("conversation_id", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rolling_summary", sa.Text(), nullable=False),
        sa.Column("current_goals", sa.JSON(), nullable=False),
        sa.Column("unfinished_work", sa.JSON(), nullable=False),
        sa.Column("recent_decisions", sa.JSON(), nullable=False),
        sa.Column("token_budget_hint", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_conversation_summaries_owner_user_id", "conversation_summaries", ["owner_user_id"]
    )
    op.create_index(
        "ix_conversation_summaries_conversation_id", "conversation_summaries", ["conversation_id"]
    )
    op.create_table(
        "planning_tasks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("manual_order", sa.Integer(), nullable=False),
        sa.Column("ai_suggested_order", sa.Integer(), nullable=False),
        sa.Column("time_estimate_minutes", sa.Integer(), nullable=False),
        sa.Column("effort_score", sa.Integer(), nullable=False),
        sa.Column("energy_score", sa.Integer(), nullable=False),
        sa.Column("focus_score", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("project_id", sa.String(120)),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for c in ["owner_user_id", "status", "deadline", "project_id"]:
        op.create_index(f"ix_planning_tasks_{c}", "planning_tasks", [c])
    op.create_table(
        "business_reminders",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("reminder_type", sa.String(40), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("related_task_id", sa.String(120)),
        sa.Column("snooze_count", sa.Integer(), nullable=False),
        sa.Column("escalation_level", sa.Integer(), nullable=False),
        sa.Column("notification_ready", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("dismissed_at", sa.DateTime(timezone=True)),
    )
    for c in ["owner_user_id", "scheduled_at", "status", "category", "related_task_id"]:
        op.create_index(f"ix_business_reminders_{c}", "business_reminders", [c])


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.6."
    )

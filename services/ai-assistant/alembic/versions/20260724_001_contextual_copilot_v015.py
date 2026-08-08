"""contextual repair copilot and business focus widget for v0.1.5

Revision ID: 20260724_001
Revises: 20260723_002
Create Date: 2026-07-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_001"
down_revision: str | None = "20260723_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_tasks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("related_repair_id", sa.String(64)),
        sa.Column("related_project_id", sa.String(64)),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("estimated_effort_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("next_action", sa.String(240)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("start_after_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("snoozed_until", sa.DateTime(timezone=True)),
        sa.Column("waiting_on_type", sa.String(40)),
        sa.Column("waiting_on_reference", sa.String(160)),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recurrence_rule_id", sa.String(64)),
        sa.Column("recurrence_occurrence_key", sa.String(80)),
        sa.Column("escalation_level", sa.Integer(), nullable=False),
        sa.Column("retention_metadata", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "owner_user_id",
            "recurrence_rule_id",
            "recurrence_occurrence_key",
            name="uq_task_recurrence_occurrence",
        ),
    )
    for col in [
        "owner_user_id",
        "related_repair_id",
        "related_project_id",
        "status",
        "due_at",
        "snoozed_until",
        "waiting_on_type",
        "recurrence_rule_id",
    ]:
        op.create_index(f"ix_business_tasks_{col}", "business_tasks", [col])
    op.create_table(
        "reminders",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("related_task_id", sa.String(64)),
        sa.Column("related_repair_id", sa.String(64)),
        sa.Column("reminder_type", sa.String(40), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger_condition", sa.String(240)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("delivery_channel", sa.String(40), nullable=False),
        sa.Column("last_delivered_at", sa.DateTime(timezone=True)),
        sa.Column("next_delivery_at", sa.DateTime(timezone=True)),
        sa.Column("snooze_count", sa.Integer(), nullable=False),
        sa.Column("escalation_level", sa.Integer(), nullable=False),
        sa.Column("quiet_hour_handling", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
    )
    for col in [
        "owner_user_id",
        "related_task_id",
        "related_repair_id",
        "scheduled_at",
        "status",
        "next_delivery_at",
    ]:
        op.create_index(f"ix_reminders_{col}", "reminders", [col])
    op.create_table(
        "recurrence_rules",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("frequency", sa.String(30), nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False),
        sa.Column("weekdays", sa.JSON(), nullable=False),
        sa.Column("day_of_month", sa.Integer()),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True)),
        sa.Column("template", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recurrence_rules_owner_user_id", "recurrence_rules", ["owner_user_id"])
    op.create_table(
        "repair_contexts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("context_mode", sa.String(30), nullable=False),
        sa.Column("customer_scope_id", sa.String(64)),
        sa.Column("device_type", sa.String(80), nullable=False),
        sa.Column("manufacturer", sa.String(80)),
        sa.Column("model", sa.String(80)),
        sa.Column("reported_issue", sa.Text(), nullable=False),
        sa.Column("current_status", sa.String(80), nullable=False),
        sa.Column("assigned_technician", sa.String(120)),
        sa.Column("customer_approval_state", sa.String(40), nullable=False),
        sa.Column("parts_state", sa.String(40), nullable=False),
        sa.Column("last_customer_update_at", sa.DateTime(timezone=True)),
        sa.Column("target_at", sa.DateTime(timezone=True)),
        sa.Column("safety_flags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repair_contexts_owner_user_id", "repair_contexts", ["owner_user_id"])
    op.create_index(
        "ix_repair_contexts_customer_scope_id", "repair_contexts", ["customer_scope_id"]
    )
    op.create_table(
        "codex_task_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("repository", sa.String(200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completion_at", sa.DateTime(timezone=True)),
        sa.Column("blocked_reason", sa.Text()),
        sa.Column("commit_sha", sa.String(80)),
        sa.Column("pull_request_reference", sa.String(200)),
        sa.Column("test_result", sa.String(120)),
        sa.Column("next_owner_action", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_codex_task_records_owner_user_id", "codex_task_records", ["owner_user_id"])
    op.create_index("ix_codex_task_records_status", "codex_task_records", ["status"])
    op.create_table(
        "notification_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("reminder_id", sa.String(64)),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("safe_summary", sa.String(240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_notification_events_owner_user_id", "notification_events", ["owner_user_id"]
    )
    op.create_index("ix_notification_events_reminder_id", "notification_events", ["reminder_id"])


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.5."
    )

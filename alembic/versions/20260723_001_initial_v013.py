"""initial durable persistence schema for v0.1.3

Revision ID: 20260723_001
Revises:
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("action_type", sa.String(80), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("resource", sa.String(160)),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("proposed_content", sa.JSON(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("action_integrity_hash", sa.String(64), nullable=False),
        sa.Column("requested_permissions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("execution_started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failed_at", sa.DateTime(timezone=True)),
        sa.Column("execution_result", sa.Text()),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_approvals_owner_user_id", "approvals", ["owner_user_id"])
    op.create_index("ix_approvals_status", "approvals", ["status"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("request_id", sa.String(120)),
        sa.Column("correlation_id", sa.String(120)),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("provider", sa.String(80)),
        sa.Column("result", sa.String(80), nullable=False),
        sa.Column("risk_level", sa.String(20)),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("source_component", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(120)),
        sa.Column("related_approval_id", sa.String(64)),
        sa.Column("related_conversation_id", sa.String(64)),
        sa.Column("related_repair_intake_id", sa.String(64)),
    )
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    op.create_index("ix_audit_events_owner_user_id", "audit_events", ["owner_user_id"])
    op.create_index("ix_audit_events_category", "audit_events", ["category"])
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("mode", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("escalation_state", sa.String(40), nullable=False),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_owner_user_id", "conversations", ["owner_user_id"])
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("conversations.id")),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("tool_summary_metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_table(
        "repair_intakes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("device_type", sa.String(80), nullable=False),
        sa.Column("manufacturer", sa.String(80)),
        sa.Column("model", sa.String(80)),
        sa.Column("issue_description", sa.Text(), nullable=False),
        sa.Column("power_state", sa.String(80)),
        sa.Column("physical_damage_state", sa.String(200)),
        sa.Column("liquid_exposure_state", sa.Boolean(), nullable=False),
        sa.Column("data_recovery_importance", sa.String(80)),
        sa.Column("preferred_service_method", sa.String(80)),
        sa.Column("desired_next_step", sa.String(120)),
        sa.Column("notes", sa.Text()),
        sa.Column("escalation_state", sa.String(40), nullable=False),
        sa.Column("escalation_reason", sa.Text()),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repair_intakes_owner_user_id", "repair_intakes", ["owner_user_id"])
    op.create_table(
        "user_preferences",
        sa.Column("owner_user_id", sa.String(120), primary_key=True),
        sa.Column("preferred_name", sa.String(120)),
        sa.Column("writing_tone", sa.String(40), nullable=False),
        sa.Column("mode", sa.String(40), nullable=False),
        sa.Column("time_zone", sa.String(80), nullable=False),
        sa.Column("quiet_hours", sa.JSON(), nullable=False),
        sa.Column("daily_briefing", sa.Boolean(), nullable=False),
        sa.Column("email_summary", sa.Boolean(), nullable=False),
        sa.Column("calendar_summary", sa.Boolean(), nullable=False),
        sa.Column("accessibility", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mock_email_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("message_id", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "message_id"),
    )
    op.create_index(
        "ix_mock_email_metadata_owner_user_id", "mock_email_metadata", ["owner_user_id"]
    )
    op.create_table(
        "mock_calendar_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.String(120), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "event_id"),
    )
    op.create_index(
        "ix_mock_calendar_metadata_owner_user_id", "mock_calendar_metadata", ["owner_user_id"]
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Destructive schema downgrade is intentionally not implemented for v0.1.3."
    )

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from nocturnix.db import Base


class ApprovalRow(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    proposed_content: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    action_integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_result: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class AuditEventRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(120))
    correlation_id: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80))
    result: Mapped[str] = mapped_column(String(80), nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    source_component: Mapped[str] = mapped_column(String(80), default="api", nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(120))
    related_approval_id: Mapped[str | None] = mapped_column(String(64))
    related_conversation_id: Mapped[str | None] = mapped_column(String(64))
    related_repair_intake_id: Mapped[str | None] = mapped_column(String(64))


class ConversationRow(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    escalation_state: Mapped[str] = mapped_column(String(40), default="none", nullable=False)
    retention_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    messages: Mapped[list[ChatMessageRow]] = relationship(back_populates="conversation")


class ChatMessageRow(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    source_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    tool_summary_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    conversation: Mapped[ConversationRow] = relationship(back_populates="messages")


class RepairIntakeRow(Base):
    __tablename__ = "repair_intakes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    device_type: Mapped[str] = mapped_column(String(80), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(80))
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    power_state: Mapped[str | None] = mapped_column(String(80))
    physical_damage_state: Mapped[str | None] = mapped_column(String(200))
    liquid_exposure_state: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_recovery_importance: Mapped[str | None] = mapped_column(String(80))
    preferred_service_method: Mapped[str | None] = mapped_column(String(80))
    desired_next_step: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    escalation_state: Mapped[str] = mapped_column(String(40), nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserPreferenceRow(Base):
    __tablename__ = "user_preferences"

    owner_user_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    preferred_name: Mapped[str | None] = mapped_column(String(120))
    writing_tone: Mapped[str] = mapped_column(String(40), default="friendly", nullable=False)
    mode: Mapped[str] = mapped_column(String(40), default="personal", nullable=False)
    time_zone: Mapped[str] = mapped_column(String(80), default="UTC", nullable=False)
    quiet_hours: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    daily_briefing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_summary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calendar_summary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accessibility: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MockEmailMetadataRow(Base):
    __tablename__ = "mock_email_metadata"
    __table_args__ = (UniqueConstraint("owner_user_id", "message_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MockCalendarMetadataRow(Base):
    __tablename__ = "mock_calendar_metadata"
    __table_args__ = (UniqueConstraint("owner_user_id", "event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    login_identifier: Mapped[str] = mapped_column(String(254), nullable=False)
    normalized_login_identifier: Mapped[str] = mapped_column(
        String(254), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    account_status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_successful_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failed_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    security_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class RoleRow(Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)


class PermissionRow(Base):
    __tablename__ = "permissions"
    name: Mapped[str] = mapped_column(String(120), primary_key=True)
    description: Mapped[str] = mapped_column(String(240), nullable=False)


class UserRoleRow(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_name: Mapped[str] = mapped_column(ForeignKey("roles.name"), primary_key=True)


class RolePermissionRow(Base):
    __tablename__ = "role_permissions"
    role_name: Mapped[str] = mapped_column(ForeignKey("roles.name"), primary_key=True)
    permission_name: Mapped[str] = mapped_column(ForeignKey("permissions.name"), primary_key=True)


class SessionRow(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    session_token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(120))
    user_agent: Mapped[str | None] = mapped_column(String(200))
    security_version: Mapped[int] = mapped_column(Integer, nullable=False)


class PasswordResetChallengeRow(Base):
    __tablename__ = "password_reset_challenges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    reset_token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ProviderAccountRow(Base):
    __tablename__ = "provider_accounts"
    __table_args__ = (UniqueConstraint("provider_name", "provider_subject_identifier"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    provider_subject_identifier: Mapped[str] = mapped_column(String(200), nullable=False)
    display_label: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized_provider_email: Mapped[str | None] = mapped_column(String(254))
    requested_scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    granted_scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_refresh_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    safe_provider_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )


class EncryptedSecretRecordRow(Base):
    __tablename__ = "encrypted_secret_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    provider_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("provider_accounts.id"), index=True
    )
    secret_type: Mapped[str] = mapped_column(String(80), nullable=False)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    encryption_algorithm: Mapped[str] = mapped_column(String(80), nullable=False)
    key_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OAuthAuthorizationStateRow(Base):
    __tablename__ = "oauth_authorization_states"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    state_token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    pkce_verifier_protected: Mapped[str] = mapped_column(String(128), nullable=False)
    pkce_challenge: Mapped[str] = mapped_column(String(128), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    requested_scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(String(200))
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False)


class BusinessTaskRow(Base):
    __tablename__ = "business_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), default="general", nullable=False)
    related_repair_id: Mapped[str | None] = mapped_column(String(64), index=True)
    related_project_id: Mapped[str | None] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    estimated_effort_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    status: Mapped[str] = mapped_column(String(30), index=True, default="inbox", nullable=False)
    next_action: Mapped[str | None] = mapped_column(String(240))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    start_after_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    waiting_on_type: Mapped[str | None] = mapped_column(String(40), index=True)
    waiting_on_reference: Mapped[str | None] = mapped_column(String(160))
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recurrence_rule_id: Mapped[str | None] = mapped_column(String(64), index=True)
    recurrence_occurrence_key: Mapped[str | None] = mapped_column(String(80))
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retention_metadata: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, nullable=False
    )


class ReminderRow(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    related_task_id: Mapped[str | None] = mapped_column(String(64), index=True)
    related_repair_id: Mapped[str | None] = mapped_column(String(64), index=True)
    reminder_type: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    trigger_condition: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), index=True, default="scheduled", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    delivery_channel: Mapped[str] = mapped_column(String(40), default="in_app_mock", nullable=False)
    last_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    snooze_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quiet_hour_handling: Mapped[str] = mapped_column(String(40), default="bundle", nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="Reminder", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RecurrenceRuleRow(Base):
    __tablename__ = "recurrence_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    frequency: Mapped[str] = mapped_column(String(30), nullable=False)
    interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    weekdays: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    day_of_month: Mapped[int | None] = mapped_column(Integer)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    template: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RepairContextRow(Base):
    __tablename__ = "repair_contexts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    context_mode: Mapped[str] = mapped_column(String(30), default="owner", nullable=False)
    customer_scope_id: Mapped[str | None] = mapped_column(String(64), index=True)
    device_type: Mapped[str] = mapped_column(String(80), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(80))
    reported_issue: Mapped[str] = mapped_column(Text, nullable=False)
    current_status: Mapped[str] = mapped_column(String(80), default="intake", nullable=False)
    assigned_technician: Mapped[str | None] = mapped_column(String(120))
    customer_approval_state: Mapped[str] = mapped_column(
        String(40), default="not_requested", nullable=False
    )
    parts_state: Mapped[str] = mapped_column(String(40), default="not_checked", nullable=False)
    last_customer_update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    target_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    safety_flags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CodexTaskRecordRow(Base):
    __tablename__ = "codex_task_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    repository: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), index=True, default="tracked", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    commit_sha: Mapped[str | None] = mapped_column(String(80))
    pull_request_reference: Mapped[str | None] = mapped_column(String(200))
    test_result: Mapped[str | None] = mapped_column(String(120))
    next_owner_action: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotificationEventRow(Base):
    __tablename__ = "notification_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    reminder_id: Mapped[str | None] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    safe_summary: Mapped[str] = mapped_column(String(240), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MemoryRow(Base):
    __tablename__ = "memories"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    visibility: Mapped[str] = mapped_column(String(40), default="private", nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)
    related_memory_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    search_vector: Mapped[str] = mapped_column(Text, default="", nullable=False)


class ConversationSummaryRow(Base):
    __tablename__ = "conversation_summaries"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    rolling_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    current_goals: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    unfinished_work: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recent_decisions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    token_budget_hint: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PlanningTaskRow(Base):
    __tablename__ = "planning_tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    manual_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    ai_suggested_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    time_estimate_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    effort_score: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    energy_score: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    focus_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    project_id: Mapped[str | None] = mapped_column(String(120), index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessReminderRow(Base):
    __tablename__ = "business_reminders"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reminder_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True, default="open", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    related_task_id: Mapped[str | None] = mapped_column(String(120), index=True)
    snooze_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notification_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AssistantTaskRow(Base):
    __tablename__ = "assistant_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id"),
        index=True,
    )
    task_type: Mapped[str] = mapped_column(
        String(40),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        index=True,
        nullable=False,
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    input_data: Mapped[dict[str, object]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    result_summary: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class AssistantResultRow(Base):
    __tablename__ = "assistant_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("assistant_tasks.id"),
        index=True,
        nullable=False,
    )
    result_type: Mapped[str] = mapped_column(
        String(40),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    content: Mapped[dict[str, object]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(String(500))
    media_type: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class AssistantPatchProposalRow(Base):
    __tablename__ = "assistant_patch_proposals"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    owner_user_id: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("assistant_tasks.id"),
        index=True,
        nullable=False,
    )
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id"),
        index=True,
    )
    repository_root: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    target_file: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    unified_diff: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    original_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    proposed_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        index=True,
        default="pending",
        nullable=False,
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    applied_by_user_id: Mapped[str | None] = mapped_column(
        String(120),
        index=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

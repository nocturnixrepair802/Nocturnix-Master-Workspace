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

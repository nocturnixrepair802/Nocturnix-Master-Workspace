from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

APP_NAME = "Nocturnix AI Assistant"
APP_VERSION = "0.1.6"
DEV_USER_ID = "dev-user-001"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    restricted = "restricted"


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    cancelled = "cancelled"
    executing = "executing"
    completed = "completed"
    failed = "failed"


class UserIdentity(StrictModel):
    user_id: str = DEV_USER_ID
    display_name: str = "Development User"
    auth_mode: str = "mock-development-only"


class StructuredError(StrictModel):
    code: str
    message: str
    request_id: str
    details: object | None = None


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    mode: Literal["personal", "business"] = "personal"
    conversation_id: str | None = Field(default=None, max_length=120)

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be empty")
        return cleaned


class SourceMetadata(StrictModel):
    source_id: str
    title: str
    excerpt: str
    relevance: float = Field(ge=0, le=1)
    placeholder: bool = False


class ChatResponse(StrictModel):
    response: str
    conversation_id: str
    sources: list[SourceMetadata] = Field(default_factory=list)
    escalation: bool = False
    proposed_actions: list[dict[str, object]] = Field(default_factory=list)
    approval_ids: list[str] = Field(default_factory=list)


class KnowledgeSearchRequest(StrictModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=5, ge=1, le=10)


class KnowledgeSearchResponse(StrictModel):
    results: list[SourceMetadata]
    placeholder: bool


class RepairIntakeRequest(StrictModel):
    device_type: str = Field(min_length=1, max_length=80)
    issue_description: str = Field(min_length=1, max_length=1000)
    manufacturer: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    power_state: str | None = Field(default=None, max_length=80)
    visible_damage: str | None = Field(default=None, max_length=200)
    liquid_exposure: bool = False
    data_recovery_importance: str | None = Field(default=None, max_length=80)
    preferred_service_method: str | None = Field(default=None, max_length=80)
    desired_next_step: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def reject_sensitive_content(self) -> RepairIntakeRequest:
        combined = " ".join(
            str(v) for v in self.model_dump().values() if isinstance(v, str)
        ).lower()
        forbidden = ["credit card", "password", "auth code", "authentication code", "ssn"]
        if any(term in combined for term in forbidden):
            raise ValueError("repair intake must not include payment data or secrets")
        return self


class RepairIntakeResponse(StrictModel):
    id: str
    owner_user_id: str
    review_ready: bool
    confirmation_state: str
    cancellation_state: str
    safety_escalation: bool
    safety_indicators: list[str]
    safety_message: str
    guarantee_notice: str


class ApprovalCreateRequest(StrictModel):
    action_type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    proposed_content: dict[str, object]
    risk_level: RiskLevel = RiskLevel.medium
    provider: str = Field(default="mock", max_length=80)
    resource: str | None = Field(default=None, max_length=160)


class ApprovalRecord(StrictModel):
    id: str = Field(default_factory=lambda: f"appr_{uuid4().hex[:12]}")
    owner_user_id: str
    action_type: str
    provider: str = "mock"
    resource: str | None = None
    title: str
    proposed_content: dict[str, object]
    risk_level: RiskLevel
    status: ApprovalStatus = ApprovalStatus.pending
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=30))
    content_hash: str = ""
    action_integrity_hash: str = ""
    requested_permissions: list[str] = Field(default_factory=list)
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    cancelled_at: datetime | None = None
    execution_started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    execution_result: str | None = None
    failure_reason: str | None = None
    version: int = 1
    decided_at: datetime | None = None
    mock_execution_result: str | None = None

    @property
    def expired(self) -> bool:
        expires = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=UTC)
        return self.status == ApprovalStatus.pending and datetime.now(UTC) >= expires


class AuditEvent(StrictModel):
    id: str = Field(default_factory=lambda: f"audit_{uuid4().hex[:12]}")
    owner_user_id: str
    category: str
    action: str
    result: str = "success"
    risk_level: RiskLevel | None = None
    resource_id: str | None = None
    related_approval_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Pagination(StrictModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class CalendarProposal(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    start: datetime
    end: datetime
    time_zone: str = Field(default="UTC", max_length=64)
    attendees: list[str] = Field(default_factory=list, max_length=10)
    location: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_window(self) -> CalendarProposal:
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class ConversationRecord(StrictModel):
    id: str = Field(default_factory=lambda: f"conv_{uuid4().hex[:12]}")
    owner_user_id: str
    mode: str = "personal"
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    escalation_state: str = "none"
    retention_expires_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + timedelta(days=30)
    )


class ChatMessageRecord(StrictModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_metadata: dict[str, object] = Field(default_factory=dict)
    tool_summary_metadata: dict[str, object] = Field(default_factory=dict)


class RepairIntakeRecord(StrictModel):
    id: str = Field(default_factory=lambda: f"repair_{uuid4().hex[:12]}")
    owner_user_id: str
    device_type: str
    manufacturer: str | None = None
    model: str | None = None
    issue_description: str
    power_state: str | None = None
    physical_damage_state: str | None = None
    liquid_exposure_state: bool = False
    data_recovery_importance: str | None = None
    preferred_service_method: str | None = None
    desired_next_step: str | None = None
    notes: str | None = None
    escalation_state: str = "none"
    escalation_reason: str | None = None
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    retention_expires_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC) + timedelta(days=90)
    )


class UserPreferences(StrictModel):
    owner_user_id: str
    preferred_name: str | None = Field(default=None, max_length=120)
    writing_tone: str = Field(default="friendly", max_length=40)
    mode: Literal["personal", "business"] = "personal"
    time_zone: str = Field(default="UTC", max_length=80)
    quiet_hours: dict[str, object] = Field(default_factory=dict)
    daily_briefing: bool = False
    email_summary: bool = True
    calendar_summary: bool = True
    accessibility: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PreferencesUpdateRequest(StrictModel):
    preferred_name: str | None = Field(default=None, max_length=120)
    writing_tone: str | None = Field(default=None, max_length=40)
    mode: Literal["personal", "business"] | None = None
    time_zone: str | None = Field(default=None, max_length=80)
    quiet_hours: dict[str, object] | None = None
    daily_briefing: bool | None = None
    email_summary: bool | None = None
    calendar_summary: bool | None = None
    accessibility: dict[str, object] | None = None


class RetentionCleanupRequest(StrictModel):
    dry_run: bool = True


class RetentionCleanupReport(StrictModel):
    dry_run: bool
    candidate_counts: dict[str, int]
    deleted_counts: dict[str, int]
    audit_recorded: bool


# v0.1.6 persistent business assistant models
class MemoryCreateRequest(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=500)
    body: str = Field(default="", max_length=5000)
    category: Literal[
        "business",
        "personal",
        "technical",
        "project",
        "customer",
        "device",
        "inventory",
        "reminder",
        "meeting",
        "research",
        "decision",
        "idea",
        "future",
    ] = "business"
    tags: list[str] = Field(default_factory=list, max_length=20)
    priority: int = Field(default=3, ge=1, le=5)
    expires_at: datetime | None = None
    visibility: Literal["private", "owner", "team_mock"] = "private"
    confidence: float = Field(default=1.0, ge=0, le=1)
    related_memory_ids: list[str] = Field(default_factory=list, max_length=20)
    source: str = Field(default="manual", max_length=120)
    ai_generated: bool = False
    manual: bool = True
    pinned: bool = False
    favorite: bool = False


class MemoryUpdateRequest(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = Field(default=None, max_length=500)
    body: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=40)
    tags: list[str] | None = Field(default=None, max_length=20)
    priority: int | None = Field(default=None, ge=1, le=5)
    expires_at: datetime | None = None
    visibility: str | None = Field(default=None, max_length=40)
    confidence: float | None = Field(default=None, ge=0, le=1)
    related_memory_ids: list[str] | None = Field(default=None, max_length=20)
    pinned: bool | None = None
    favorite: bool | None = None
    archived: bool | None = None
    deleted: bool | None = None


class PlanningTaskRequest(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: Literal[
        "today", "this_week", "upcoming", "waiting", "blocked", "completed", "cancelled", "deferred"
    ] = "today"
    priority: int = Field(default=3, ge=1, le=5)
    manual_order: int = Field(default=100, ge=0)
    ai_suggested_order: int = Field(default=100, ge=0)
    time_estimate_minutes: int = Field(default=15, ge=1, le=1440)
    effort_score: int = Field(default=3, ge=1, le=5)
    energy_score: int = Field(default=3, ge=1, le=5)
    deadline: datetime | None = None
    project_id: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ReminderRequest(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=2000)
    reminder_type: Literal[
        "one_time",
        "daily",
        "weekly",
        "monthly",
        "yearly",
        "after_event",
        "after_approval",
        "after_inactivity",
    ] = "one_time"
    scheduled_at: datetime | None = None
    priority: int = Field(default=3, ge=1, le=5)
    category: str = Field(default="reminder", max_length=80)
    related_task_id: str | None = Field(default=None, max_length=120)


class NaturalCommandRequest(StrictModel):
    command: str = Field(min_length=1, max_length=1000)


class AssistantTaskStatus(StrEnum):
    queued = "queued"
    running = "running"
    waiting_for_approval = "waiting_for_approval"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class AssistantTaskType(StrEnum):
    research = "research"
    spreadsheet = "spreadsheet"
    repair_action = "repair_action"
    general = "general"


class AssistantTaskCreateRequest(StrictModel):
    task_type: AssistantTaskType
    title: str = Field(min_length=1, max_length=200)
    instructions: str = Field(min_length=1, max_length=5000)
    conversation_id: str | None = Field(default=None, max_length=64)
    input_data: dict[str, object] = Field(default_factory=dict)


class AssistantTaskResponse(StrictModel):
    id: str
    owner_user_id: str
    conversation_id: str | None = None
    task_type: AssistantTaskType
    title: str
    instructions: str
    status: AssistantTaskStatus
    progress_percent: int
    input_data: dict[str, object]
    result_summary: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime

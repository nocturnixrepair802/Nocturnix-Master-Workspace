from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, select, update
from sqlalchemy.orm import Session

from nocturnix.models import (
    ApprovalRecord,
    ApprovalStatus,
    AuditEvent,
    ChatMessageRecord,
    ConversationRecord,
    RepairIntakeRecord,
    RiskLevel,
    UserPreferences,
)
from nocturnix.persistence_models import (
    ApprovalRow,
    AuditEventRow,
    ChatMessageRow,
    ConversationRow,
    MockCalendarMetadataRow,
    MockEmailMetadataRow,
    RepairIntakeRow,
    UserPreferenceRow,
)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def action_integrity(approval: ApprovalRecord) -> str:
    return canonical_hash(
        {
            "action_type": approval.action_type,
            "provider": approval.provider,
            "resource": approval.resource,
            "content_hash": approval.content_hash,
        }
    )


def _risk(value: str | None) -> RiskLevel | None:
    return RiskLevel(value) if value else None


class SqlApprovalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_model(self, row: ApprovalRow) -> ApprovalRecord:
        return ApprovalRecord(
            id=row.id,
            owner_user_id=row.owner_user_id,
            action_type=row.action_type,
            provider=row.provider,
            resource=row.resource,
            title=row.title,
            proposed_content=row.proposed_content,
            risk_level=RiskLevel(row.risk_level),
            status=ApprovalStatus(row.status),
            content_hash=row.content_hash,
            action_integrity_hash=row.action_integrity_hash,
            requested_permissions=row.requested_permissions,
            created_at=row.created_at,
            expires_at=row.expires_at,
            approved_at=row.approved_at,
            rejected_at=row.rejected_at,
            cancelled_at=row.cancelled_at,
            execution_started_at=row.execution_started_at,
            completed_at=row.completed_at,
            failed_at=row.failed_at,
            execution_result=row.execution_result,
            failure_reason=row.failure_reason,
            version=row.version,
            decided_at=row.approved_at or row.rejected_at or row.cancelled_at,
            mock_execution_result=row.execution_result,
        )

    def add(self, approval: ApprovalRecord) -> ApprovalRecord:
        approval.content_hash = approval.content_hash or canonical_hash(approval.proposed_content)
        approval.action_integrity_hash = approval.action_integrity_hash or action_integrity(
            approval
        )
        self.session.add(
            ApprovalRow(
                id=approval.id,
                owner_user_id=approval.owner_user_id,
                action_type=approval.action_type,
                provider=approval.provider,
                resource=approval.resource,
                title=approval.title,
                proposed_content=approval.proposed_content,
                risk_level=approval.risk_level.value,
                status=approval.status.value,
                content_hash=approval.content_hash,
                action_integrity_hash=approval.action_integrity_hash,
                requested_permissions=approval.requested_permissions,
                created_at=approval.created_at,
                expires_at=approval.expires_at,
                approved_at=approval.approved_at,
                rejected_at=approval.rejected_at,
                cancelled_at=approval.cancelled_at,
                execution_started_at=approval.execution_started_at,
                completed_at=approval.completed_at,
                failed_at=approval.failed_at,
                execution_result=approval.execution_result,
                failure_reason=approval.failure_reason,
                version=approval.version,
            )
        )
        self.session.flush()
        return approval

    def get(self, approval_id: str) -> ApprovalRecord | None:
        row = self.session.get(ApprovalRow, approval_id)
        return self._to_model(row) if row else None

    def update(self, approval: ApprovalRecord) -> ApprovalRecord:
        row = self.session.get(ApprovalRow, approval.id)
        if row is None:
            raise KeyError(approval.id)
        if canonical_hash(approval.proposed_content) != row.content_hash:
            raise ValueError("approval proposed content hash mismatch")
        if action_integrity(approval) != row.action_integrity_hash:
            raise ValueError("approval action integrity hash mismatch")
        row.status = approval.status.value
        row.approved_at = approval.approved_at
        row.rejected_at = approval.rejected_at
        row.cancelled_at = approval.cancelled_at
        row.execution_started_at = approval.execution_started_at
        row.completed_at = approval.completed_at
        row.failed_at = approval.failed_at
        row.execution_result = approval.execution_result or approval.mock_execution_result
        row.failure_reason = approval.failure_reason
        row.version += 1
        approval.version = row.version
        self.session.flush()
        return approval

    def list_for_user(
        self, user_id: str, offset: int = 0, limit: int = 100
    ) -> list[ApprovalRecord]:
        stmt = (
            select(ApprovalRow)
            .where(ApprovalRow.owner_user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        return [self._to_model(row) for row in self.session.scalars(stmt)]

    def claim_execution(self, approval_id: str, owner_user_id: str) -> ApprovalRecord | None:
        now = datetime.now(UTC)
        result: Any = self.session.execute(
            update(ApprovalRow)
            .where(
                ApprovalRow.id == approval_id,
                ApprovalRow.owner_user_id == owner_user_id,
                ApprovalRow.status == ApprovalStatus.pending.value,
                ApprovalRow.execution_started_at.is_(None),
                ApprovalRow.expires_at > now,
            )
            .values(
                status=ApprovalStatus.executing.value,
                execution_started_at=now,
                version=ApprovalRow.version + 1,
            )
        )
        self.session.flush()
        if result.rowcount != 1:
            return None
        return self.get(approval_id)


class SqlAuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: AuditEvent) -> AuditEvent:
        self.session.add(
            AuditEventRow(
                id=event.id,
                created_at=event.created_at,
                owner_user_id=event.owner_user_id,
                request_id=event.request_id,
                correlation_id=event.correlation_id,
                category=event.category,
                event_type=event.action,
                action=event.action,
                provider=None,
                result=event.result,
                risk_level=event.risk_level.value if event.risk_level else None,
                metadata_json=event.metadata,
                source_component="service",
                resource_id=event.resource_id,
                related_approval_id=event.related_approval_id,
                related_conversation_id=None,
                related_repair_intake_id=None,
            )
        )
        self.session.flush()
        return event

    def list_for_user(
        self, user_id: str, category: str | None, offset: int, limit: int
    ) -> list[AuditEvent]:
        stmt: Select[tuple[AuditEventRow]] = select(AuditEventRow).where(
            AuditEventRow.owner_user_id == user_id
        )
        if category:
            stmt = stmt.where(AuditEventRow.category == category)
        rows = self.session.scalars(
            stmt.order_by(AuditEventRow.created_at).offset(offset).limit(limit)
        ).all()
        return [
            AuditEvent(
                id=r.id,
                owner_user_id=r.owner_user_id,
                category=r.category,
                action=r.action,
                result=r.result,
                risk_level=_risk(r.risk_level),
                resource_id=r.resource_id,
                related_approval_id=r.related_approval_id,
                correlation_id=r.correlation_id,
                request_id=r.request_id,
                metadata=r.metadata_json,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def count_candidates(self, before_iso: str) -> int:
        before = datetime.fromisoformat(before_iso)
        return len(
            self.session.scalars(
                select(AuditEventRow.id).where(AuditEventRow.created_at < before)
            ).all()
        )


class SqlConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_model(self, r: ConversationRow) -> ConversationRecord:
        return ConversationRecord(
            id=r.id,
            owner_user_id=r.owner_user_id,
            mode=r.mode,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            escalation_state=r.escalation_state,
            retention_expires_at=r.retention_expires_at,
        )

    def get(self, conversation_id: str) -> ConversationRecord | None:
        r = self.session.get(ConversationRow, conversation_id)
        return self._to_model(r) if r else None

    def add(self, c: ConversationRecord) -> ConversationRecord:
        self.session.add(
            ConversationRow(
                id=c.id,
                owner_user_id=c.owner_user_id,
                mode=c.mode,
                status=c.status,
                created_at=c.created_at,
                updated_at=c.updated_at,
                escalation_state=c.escalation_state,
                retention_expires_at=c.retention_expires_at,
            )
        )
        self.session.flush()
        return c

    def update(self, c: ConversationRecord) -> ConversationRecord:
        r = self.session.get(ConversationRow, c.id)
        assert r is not None
        r.updated_at = c.updated_at
        r.status = c.status
        r.escalation_state = c.escalation_state
        self.session.flush()
        return c

    def list_for_user(self, user_id: str, offset: int, limit: int) -> list[ConversationRecord]:
        return [
            self._to_model(r)
            for r in self.session.scalars(
                select(ConversationRow)
                .where(ConversationRow.owner_user_id == user_id)
                .offset(offset)
                .limit(limit)
            )
        ]


class SqlMessageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, m: ChatMessageRecord) -> ChatMessageRecord:
        self.session.add(
            ChatMessageRow(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
                source_metadata=m.source_metadata,
                tool_summary_metadata=m.tool_summary_metadata,
            )
        )
        self.session.flush()
        return m

    def list_for_conversation(self, conversation_id: str) -> list[ChatMessageRecord]:
        rows = self.session.scalars(
            select(ChatMessageRow)
            .where(ChatMessageRow.conversation_id == conversation_id)
            .order_by(ChatMessageRow.created_at)
        ).all()
        return [
            ChatMessageRecord(
                id=r.id,
                conversation_id=r.conversation_id,
                role=r.role,  # type: ignore[arg-type]
                content=r.content,
                created_at=r.created_at,
                source_metadata=r.source_metadata,
                tool_summary_metadata=r.tool_summary_metadata,
            )
            for r in rows
        ]  # type: ignore[arg-type]


class SqlRepairIntakeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_model(self, r: RepairIntakeRow) -> RepairIntakeRecord:
        return RepairIntakeRecord(
            id=r.id,
            owner_user_id=r.owner_user_id,
            device_type=r.device_type,
            manufacturer=r.manufacturer,
            model=r.model,
            issue_description=r.issue_description,
            power_state=r.power_state,
            physical_damage_state=r.physical_damage_state,
            liquid_exposure_state=r.liquid_exposure_state,
            data_recovery_importance=r.data_recovery_importance,
            preferred_service_method=r.preferred_service_method,
            desired_next_step=r.desired_next_step,
            notes=r.notes,
            escalation_state=r.escalation_state,
            escalation_reason=r.escalation_reason,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            confirmed_at=r.confirmed_at,
            cancelled_at=r.cancelled_at,
            retention_expires_at=r.retention_expires_at,
        )

    def add(self, i: RepairIntakeRecord) -> RepairIntakeRecord:
        self.session.add(RepairIntakeRow(**i.model_dump()))
        self.session.flush()
        return i

    def get(self, intake_id: str) -> RepairIntakeRecord | None:
        r = self.session.get(RepairIntakeRow, intake_id)
        return self._to_model(r) if r else None

    def list_for_user(self, user_id: str, offset: int, limit: int) -> list[RepairIntakeRecord]:
        return [
            self._to_model(r)
            for r in self.session.scalars(
                select(RepairIntakeRow)
                .where(RepairIntakeRow.owner_user_id == user_id)
                .offset(offset)
                .limit(limit)
            )
        ]


class SqlPreferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: str) -> UserPreferences | None:
        r = self.session.get(UserPreferenceRow, user_id)
        return (
            UserPreferences(
                owner_user_id=r.owner_user_id,
                preferred_name=r.preferred_name,
                writing_tone=r.writing_tone,
                mode=r.mode,  # type: ignore[arg-type]
                time_zone=r.time_zone,
                quiet_hours=r.quiet_hours,
                daily_briefing=r.daily_briefing,
                email_summary=r.email_summary,
                calendar_summary=r.calendar_summary,
                accessibility=r.accessibility,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            if r
            else None
        )  # type: ignore[arg-type]

    def upsert(self, p: UserPreferences) -> UserPreferences:
        r = self.session.get(UserPreferenceRow, p.owner_user_id)
        if r is None:
            self.session.add(UserPreferenceRow(**p.model_dump()))
        else:
            for k, v in p.model_dump().items():
                setattr(r, k, v)
        self.session.flush()
        return p


class SqlMockMetadataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_email(self, user_id: str, message_id: str, metadata: dict[str, object]) -> None:
        now = datetime.now(UTC)
        self.session.add(
            MockEmailMetadataRow(
                owner_user_id=user_id,
                message_id=message_id,
                metadata_json=metadata,
                created_at=now,
                updated_at=now,
            )
        )
        self.session.flush()

    def upsert_calendar(self, user_id: str, event_id: str, metadata: dict[str, object]) -> None:
        now = datetime.now(UTC)
        self.session.add(
            MockCalendarMetadataRow(
                owner_user_id=user_id,
                event_id=event_id,
                metadata_json=metadata,
                created_at=now,
                updated_at=now,
            )
        )
        self.session.flush()

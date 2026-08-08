from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from nocturnix.models import (
    ApprovalCreateRequest,
    ApprovalRecord,
    ApprovalStatus,
    AuditEvent,
    ChatRequest,
    ChatResponse,
    RepairIntakeRequest,
    RepairIntakeResponse,
    RiskLevel,
    SourceMetadata,
    UserIdentity,
)

SENSITIVE_KEYS = ("password", "token", "secret", "card", "ssn", "auth", "imei", "serial")
SAFETY_TERMS = {
    "battery_swelling": ("swelling", "bulging", "expanded battery"),
    "smoke": ("smoke", "smoking"),
    "burning_smell": ("burning smell", "burnt smell", "burning odor"),
    "severe_overheating": ("severe overheating", "very hot", "overheating"),
    "liquid_exposure": ("liquid", "water", "spill", "submerged"),
}
PROMPT_ATTACKS = (
    "ignore previous",
    "system prompt",
    "reveal prompt",
    "bypass approval",
    "show secrets",
)


class PermissionDenied(Exception):
    pass


class NotFound(Exception):
    pass


class ApprovalConflict(Exception):
    pass


def redact_metadata(metadata: dict[str, object]) -> dict[str, object]:
    return {
        key: "[REDACTED]" if any(term in key.lower() for term in SENSITIVE_KEYS) else value
        for key, value in metadata.items()
    }


class AuditService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def record(
        self,
        user: UserIdentity,
        category: str,
        action: str,
        *,
        result: str = "success",
        risk_level: RiskLevel | None = None,
        resource_id: str | None = None,
        related_approval_id: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            owner_user_id=user.user_id,
            category=category,
            action=action,
            result=result,
            risk_level=risk_level,
            resource_id=resource_id,
            related_approval_id=related_approval_id,
            request_id=request_id,
            correlation_id=correlation_id,
            metadata=redact_metadata(metadata or {}),
        )
        return self.repo.add(event)

    def list(
        self, user: UserIdentity, category: str | None, offset: int, limit: int
    ) -> list[AuditEvent]:
        return self.repo.list_for_user(user.user_id, category, offset, min(limit, 100))


class ApprovalService:
    def __init__(self, repo, audit: AuditService) -> None:
        self.repo = repo
        self.audit = audit

    def create(self, user: UserIdentity, req: ApprovalCreateRequest) -> ApprovalRecord:
        approval = ApprovalRecord(
            owner_user_id=user.user_id,
            action_type=req.action_type,
            provider=req.provider,
            resource=req.resource,
            title=req.title,
            proposed_content=req.proposed_content,
            risk_level=req.risk_level,
        )
        self.repo.add(approval)
        self.audit.record(
            user,
            "approval",
            "created",
            risk_level=req.risk_level,
            resource_id=approval.id,
            related_approval_id=approval.id,
        )
        return approval

    def get(self, user: UserIdentity, approval_id: str) -> ApprovalRecord:
        approval = self.repo.get(approval_id)
        if approval is None:
            raise NotFound("approval not found")
        if approval.owner_user_id != user.user_id:
            raise PermissionDenied("approval belongs to another user")
        if approval.expired:
            approval.status = ApprovalStatus.expired
            self.repo.update(approval)
        return approval

    def list(self, user: UserIdentity) -> list[ApprovalRecord]:
        return [self.get(user, item.id) for item in self.repo.list_for_user(user.user_id)]

    def approve(self, user: UserIdentity, approval_id: str) -> ApprovalRecord:
        approval = self.get(user, approval_id)
        if approval.status != ApprovalStatus.pending:
            raise ApprovalConflict("approval is not pending")
        if approval.expired:
            approval.status = ApprovalStatus.expired
            self.repo.update(approval)
            raise ApprovalConflict("approval has expired")
        now = datetime.now(UTC)
        claimed = self.repo.claim_execution(approval.id, user.user_id)
        if claimed is None:
            raise ApprovalConflict("approval is not pending")
        approval = claimed
        approval.status = ApprovalStatus.approved
        approval.approved_at = now
        approval.completed_at = now
        approval.decided_at = now
        approval.execution_result = "mock execution recorded; no external action was taken"
        approval.mock_execution_result = approval.execution_result
        self.repo.update(approval)
        self.audit.record(
            user,
            "approval",
            "approved",
            risk_level=approval.risk_level,
            resource_id=approval.id,
            related_approval_id=approval.id,
            metadata={"mock_execution": True},
        )
        return approval

    def reject(self, user: UserIdentity, approval_id: str) -> ApprovalRecord:
        approval = self.get(user, approval_id)
        if approval.status != ApprovalStatus.pending:
            raise ApprovalConflict("approval is not pending")
        approval.status = ApprovalStatus.rejected
        approval.rejected_at = datetime.now(UTC)
        approval.decided_at = approval.rejected_at
        self.repo.update(approval)
        self.audit.record(user, "approval", "rejected", resource_id=approval.id)
        return approval


class KnowledgeService:
    def __init__(self, knowledge_path: Path) -> None:
        self.knowledge_path = knowledge_path

    def search(self, query: str, limit: int = 5) -> tuple[list[SourceMetadata], bool]:
        query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        results: list[SourceMetadata] = []
        for path in (
            sorted(self.knowledge_path.glob("*.md")) if self.knowledge_path.exists() else []
        ):
            text = path.read_text(encoding="utf-8")
            title = next(
                (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")),
                path.stem,
            )
            body_terms = set(re.findall(r"[a-z0-9]+", text.lower()))
            overlap = len(query_terms & body_terms)
            if overlap:
                excerpt = " ".join(text.split())[:240]
                results.append(
                    SourceMetadata(
                        source_id=f"kb-{path.stem}",
                        title=title,
                        excerpt=excerpt,
                        relevance=min(1.0, overlap / max(len(query_terms), 1)),
                    )
                )
        results.sort(key=lambda item: item.relevance, reverse=True)
        if not results:
            return [
                SourceMetadata(
                    source_id="kb-placeholder",
                    title="No approved source found",
                    excerpt="No approved local knowledge matched this request.",
                    relevance=0,
                    placeholder=True,
                )
            ], True
        return results[:limit], False


class MockAssistantProvider:
    def respond(
        self, message: str, conversation_id: str | None, sources: list[SourceMetadata]
    ) -> ChatResponse:
        lowered = message.lower()
        attack = any(term in lowered for term in PROMPT_ATTACKS)
        if attack:
            response = (
                "I cannot reveal system prompts, secrets, or bypass approval controls. "
                "I can continue with safe development-only help."
            )
        elif sources and not sources[0].placeholder:
            response = (
                "Mock assistant response based on local placeholder knowledge. "
                "No live provider was called."
            )
        else:
            response = (
                "I do not have reliable approved knowledge for that request. "
                "No live provider was called."
            )
        return ChatResponse(
            response=response,
            conversation_id=conversation_id or f"conv_{uuid4().hex[:12]}",
            sources=sources,
            escalation=attack,
        )


class RepairService:
    def create(
        self, user: UserIdentity, req: RepairIntakeRequest, audit: AuditService
    ) -> RepairIntakeResponse:
        text = " ".join(
            [req.issue_description, str(req.visible_damage or ""), str(req.notes or "")]
        ).lower()
        indicators = [
            name
            for name, terms in SAFETY_TERMS.items()
            if req.liquid_exposure
            and name == "liquid_exposure"
            or any(term in text for term in terms)
        ]
        escalation = bool(indicators)
        audit.record(user, "repair", "created", metadata={"safety_escalation": escalation})
        return RepairIntakeResponse(
            id=f"repair_{uuid4().hex[:12]}",
            owner_user_id=user.user_id,
            review_ready=True,
            confirmation_state="draft",
            cancellation_state="available",
            safety_escalation=escalation,
            safety_indicators=indicators,
            safety_message=(
                (
                    "Stop using the device, keep it away from flammable materials, and seek "
                    "professional help."
                )
                if escalation
                else "No urgent safety escalation detected from the provided details."
            ),
            guarantee_notice=(
                "This mock intake does not guarantee price, repairability, completion time, "
                "or data recovery."
            ),
        )


class ConversationService:
    def __init__(self, conversations, messages, retention_days: int) -> None:
        self.conversations = conversations
        self.messages = messages
        self.retention_days = retention_days

    def persist_exchange(
        self, user: UserIdentity, req: ChatRequest, response: ChatResponse
    ) -> None:
        from datetime import timedelta

        from nocturnix.models import ChatMessageRecord, ConversationRecord

        now = datetime.now(UTC)
        conversation = self.conversations.get(response.conversation_id)
        if conversation is None:
            conversation = ConversationRecord(
                id=response.conversation_id,
                owner_user_id=user.user_id,
                mode=req.mode,
                escalation_state="escalated" if response.escalation else "none",
                retention_expires_at=now + timedelta(days=self.retention_days),
            )
            self.conversations.add(conversation)
        elif conversation.owner_user_id != user.user_id:
            raise PermissionDenied("conversation belongs to another user")
        else:
            conversation.updated_at = now
            if response.escalation:
                conversation.escalation_state = "escalated"
            self.conversations.update(conversation)
        self.messages.add(
            ChatMessageRecord(conversation_id=conversation.id, role="user", content=req.message)
        )
        self.messages.add(
            ChatMessageRecord(
                conversation_id=conversation.id,
                role="assistant",
                content=response.response,
                source_metadata={"source_count": len(response.sources)},
                tool_summary_metadata={"mock_provider": True},
            )
        )


class PreferenceService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def get(self, user: UserIdentity):
        from nocturnix.models import UserPreferences

        return self.repo.get(user.user_id) or UserPreferences(owner_user_id=user.user_id)

    def update(self, user: UserIdentity, req):
        current = self.get(user)
        data = current.model_dump()
        for key, value in req.model_dump(exclude_unset=True).items():
            if value is not None:
                data[key] = value
        data["owner_user_id"] = user.user_id
        data["created_at"] = current.created_at
        data["updated_at"] = datetime.now(UTC)
        return self.repo.upsert(type(current)(**data))


class RetentionService:
    def __init__(self, audit: AuditService, settings) -> None:
        self.audit = audit
        self.settings = settings

    def cleanup(self, user: UserIdentity, dry_run: bool = True):
        from datetime import timedelta

        from nocturnix.models import RetentionCleanupReport

        now = datetime.now(UTC)
        candidate_counts = {
            "audit_events": self.audit.repo.count_candidates(
                (now - timedelta(days=self.settings.audit_retention_days)).isoformat()
            ),
            "conversations": 0,
            "repair_intakes": 0,
            "approvals": 0,
        }
        self.audit.record(
            user,
            "retention",
            "cleanup_dry_run" if dry_run else "cleanup_requested",
            metadata={"candidate_counts": candidate_counts, "physical_delete_enabled": False},
        )
        return RetentionCleanupReport(
            dry_run=dry_run,
            candidate_counts=candidate_counts,
            deleted_counts={k: 0 for k in candidate_counts},
            audit_recorded=True,
        )

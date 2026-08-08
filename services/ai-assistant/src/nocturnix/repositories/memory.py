from __future__ import annotations

from nocturnix.models import ApprovalRecord, AuditEvent


class InMemoryApprovalRepository:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalRecord] = {}

    def add(self, approval: ApprovalRecord) -> ApprovalRecord:
        self._items[approval.id] = approval.model_copy(deep=True)
        return approval

    def get(self, approval_id: str) -> ApprovalRecord | None:
        item = self._items.get(approval_id)
        return item.model_copy(deep=True) if item else None

    def update(self, approval: ApprovalRecord) -> ApprovalRecord:
        self._items[approval.id] = approval.model_copy(deep=True)
        return approval

    def claim_execution(self, approval_id: str, owner_user_id: str) -> ApprovalRecord | None:
        item = self._items.get(approval_id)
        if (
            item is None
            or item.owner_user_id != owner_user_id
            or item.status != "pending"
            or item.execution_started_at is not None
            or item.expired
        ):
            return None
        from datetime import UTC, datetime

        item.execution_started_at = datetime.now(UTC)
        from nocturnix.models import ApprovalStatus

        item.status = ApprovalStatus.executing
        item.version += 1
        return item.model_copy(deep=True)

    def list_for_user(
        self, user_id: str, offset: int = 0, limit: int = 100
    ) -> list[ApprovalRecord]:
        return [
            item.model_copy(deep=True)
            for item in self._items.values()
            if item.owner_user_id == user_id
        ][offset : offset + limit]


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self._items: list[AuditEvent] = []

    def add(self, event: AuditEvent) -> AuditEvent:
        self._items.append(event.model_copy(deep=True))
        return event

    def count_candidates(self, before_iso: str) -> int:
        from datetime import datetime

        before = datetime.fromisoformat(before_iso)
        return len([e for e in self._items if e.created_at < before])

    def list_for_user(
        self, user_id: str, category: str | None, offset: int, limit: int
    ) -> list[AuditEvent]:
        items = [
            event.model_copy(deep=True)
            for event in self._items
            if event.owner_user_id == user_id and (category is None or event.category == category)
        ]
        return items[offset : offset + limit]

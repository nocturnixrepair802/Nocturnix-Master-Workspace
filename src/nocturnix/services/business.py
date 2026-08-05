from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, cast
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from nocturnix.persistence.models import (
    BusinessTaskRow,
    NotificationEventRow,
    ReminderRow,
)

PRIORITY_SCORE = {"urgent": 50, "high": 30, "normal": 10, "low": 0}
WAITING_TYPES = {
    "customer",
    "supplier",
    "part",
    "approval",
    "payment",
    "appointment",
    "codex_task",
    "pull_request_review",
    "external_response",
}


def now_utc() -> datetime:
    return datetime.now(UTC)


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def safe_task(row: BusinessTaskRow) -> dict[str, object]:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def redacted_summary(text: str) -> str:
    banned = ["password", "token", "secret", "card", "ssn"]
    safe = text[:180]
    return "[REDACTED REMINDER]" if any(b in safe.lower() for b in banned) else safe


class NotificationProvider(Protocol):
    name: str

    def deliver(self, session: Session, reminder: ReminderRow) -> NotificationEventRow: ...


class InAppMockNotificationProvider:
    name = "in_app_mock"

    def deliver(self, session: Session, reminder: ReminderRow) -> NotificationEventRow:
        event = NotificationEventRow(
            id=make_id("notif"),
            owner_user_id=reminder.owner_user_id,
            reminder_id=reminder.id,
            provider=self.name,
            channel="in_app",
            status="mock_delivered",
            safe_summary=redacted_summary(reminder.title),
            created_at=now_utc(),
        )
        reminder.last_delivered_at = event.created_at
        session.add(event)
        return event


class BusinessService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tasks(self, owner: str, status: str | None = None) -> list[dict[str, object]]:
        stmt = select(BusinessTaskRow).where(BusinessTaskRow.owner_user_id == owner)
        if status:
            stmt = stmt.where(BusinessTaskRow.status == status)
        return [
            safe_task(r)
            for r in self.session.scalars(stmt.order_by(BusinessTaskRow.created_at.desc())).all()
        ]

    def create_task(self, owner: str, data: dict[str, object]) -> dict[str, object]:
        now = now_utc()
        row = BusinessTaskRow(
            id=make_id("task"),
            owner_user_id=owner,
            title=str(data.get("title") or "Untitled task")[:200],
            description=data.get("description"),
            category=str(data.get("category") or "general"),
            related_repair_id=data.get("related_repair_id"),
            related_project_id=data.get("related_project_id"),
            priority=str(data.get("priority") or "normal"),
            estimated_effort_minutes=int(cast(Any, data.get("estimated_effort_minutes") or 15)),
            status=str(data.get("status") or "inbox"),
            next_action=data.get("next_action"),
            due_at=data.get("due_at"),
            start_after_at=data.get("start_after_at"),
            waiting_on_type=data.get("waiting_on_type"),
            waiting_on_reference=data.get("waiting_on_reference"),
            source=str(data.get("source") or "manual"),
            created_at=now,
            updated_at=now,
            escalation_level=int(cast(Any, data.get("escalation_level") or 0)),
            retention_metadata=data.get("retention_metadata") or {},
        )
        self.session.add(row)
        self.session.flush()
        return safe_task(row)

    def complete(self, owner: str, task_id: str) -> dict[str, object]:
        row = self._task(owner, task_id)
        row.status = "completed"
        row.completed_at = now_utc()
        row.updated_at = row.completed_at
        return safe_task(row)

    def snooze(self, owner: str, task_id: str, until: datetime) -> dict[str, object]:
        row = self._task(owner, task_id)
        row.status = "deferred"
        row.snoozed_until = until
        row.updated_at = now_utc()
        return safe_task(row)

    def reschedule(self, owner: str, task_id: str, due_at: datetime) -> dict[str, object]:
        row = self._task(owner, task_id)
        row.due_at = due_at
        row.status = "planned"
        row.updated_at = now_utc()
        return safe_task(row)

    def _task(self, owner: str, task_id: str) -> BusinessTaskRow:
        row = self.session.get(BusinessTaskRow, task_id)
        if not row or row.owner_user_id != owner:
            raise KeyError("task not found")
        return row

    def waiting_on(self, owner: str, too_long_days: int = 3) -> dict[str, object]:
        rows = self.session.scalars(
            select(BusinessTaskRow).where(
                BusinessTaskRow.owner_user_id == owner, BusinessTaskRow.status == "waiting"
            )
        ).all()
        cutoff = now_utc() - timedelta(days=too_long_days)
        return {
            "items": [safe_task(r) for r in rows],
            "waiting_too_long": [safe_task(r) for r in rows if aware(r.updated_at) < cutoff],
            "follow_up_today": [
                safe_task(r)
                for r in rows
                if r.due_at and aware(r.due_at) <= now_utc() + timedelta(days=1)
            ],
        }

    def focus_now(
        self, owner: str, available_minutes: int = 30, limit: int = 3
    ) -> dict[str, object]:
        now = now_utc()
        rows = self.session.scalars(
            select(BusinessTaskRow).where(
                BusinessTaskRow.owner_user_id == owner,
                BusinessTaskRow.status.in_(["inbox", "planned", "ready", "in_progress"]),
                or_(BusinessTaskRow.snoozed_until.is_(None), BusinessTaskRow.snoozed_until <= now),
            )
        ).all()
        scored = []
        for r in rows:
            score = PRIORITY_SCORE.get(r.priority, 10) + r.escalation_level * 20
            reasons = []
            due_at = aware(r.due_at) if r.due_at else None
            if due_at and due_at < now:
                score += 60
                reasons.append(
                    "overdue customer follow-up" if r.category == "repair" else "overdue"
                )
            elif due_at and due_at.date() == now.date():
                score += 35
                reasons.append("due today")
            if r.estimated_effort_minutes <= 5:
                score += 15
                reasons.append("quick task under five minutes")
            if r.related_repair_id:
                score += 10
                reasons.append("customer impact")
            if r.estimated_effort_minutes > available_minutes:
                score -= 20
            scored.append((score, r, reasons or ["clear next action"]))
        scored.sort(key=lambda x: (-x[0], x[1].estimated_effort_minutes, x[1].created_at))
        return {
            "items": [
                {"task": safe_task(r), "score": score, "explanations": reasons[:3]}
                for score, r, reasons in scored[: min(limit, 3)]
            ],
            "mock": True,
        }

    def briefing(self, owner: str) -> dict[str, object]:
        focus = cast(list[dict[str, Any]], self.focus_now(owner)["items"])
        waiting = cast(dict[str, list[dict[str, Any]]], self.waiting_on(owner))
        quick = next((i for i in focus if i["task"]["estimated_effort_minutes"] <= 5), None)
        return {
            "focus_items": focus,
            "appointments_placeholder": [],
            "customer_follow_ups": waiting["follow_up_today"],
            "repairs_waiting_on_parts": [
                i for i in waiting["items"] if i["waiting_on_type"] == "part"
            ],
            "repairs_waiting_on_approval": [
                i for i in waiting["items"] if i["waiting_on_type"] == "approval"
            ],
            "overdue_invoices_placeholder": [],
            "parts_expected_placeholder": [],
            "codex_tasks_awaiting_review": [],
            "quick_win": quick,
            "possible_risk_or_stalled_item": (
                waiting["waiting_too_long"] or [cast(dict[str, Any], {})]
            )[0],
            "items_completed_recently": self.list_tasks(owner, "completed")[:5],
            "mock": True,
        }

    def end_of_day(self, owner: str) -> dict[str, object]:
        tasks = cast(list[dict[str, Any]], self.list_tasks(owner))
        return {
            "completed_tasks": [t for t in tasks if t["status"] == "completed"],
            "unfinished_tasks": [t for t in tasks if t["status"] not in {"completed", "cancelled"}],
            "waiting_on_items": [t for t in tasks if t["status"] == "waiting"],
            "overdue_items": [t for t in tasks if t["due_at"] and aware(t["due_at"]) < now_utc()],
            "tomorrow_candidates": [
                t for t in tasks if t["status"] in {"inbox", "planned", "ready"}
            ][:5],
            "items_with_no_clear_next_action": [
                t
                for t in tasks
                if not t["next_action"] and t["status"] not in {"completed", "cancelled"}
            ],
            "recovery_choices": [
                "move_to_tomorrow",
                "reschedule",
                "mark_waiting",
                "break_into_smaller_task",
                "cancel",
                "retain_in_inbox",
            ],
        }

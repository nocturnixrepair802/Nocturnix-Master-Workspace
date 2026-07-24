from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from nocturnix.repair_persistence_models import RepairConfirmationRow


class RepairConfirmationError(Exception):
    """Base error for repair action confirmation failures."""


class RepairConfirmationNotFound(RepairConfirmationError):
    pass


class RepairConfirmationExpired(RepairConfirmationError):
    pass


class RepairConfirmationConsumed(RepairConfirmationError):
    pass


@dataclass(frozen=True)
class PendingRepairConfirmation:
    id: str
    owner_user_id: str
    previous_response_id: str
    tool_name: str
    arguments: dict[str, Any]
    action_key: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None


class RepairConfirmationStore:
    """Thread-safe process-local store retained for isolated tests."""

    def __init__(self, *, ttl_seconds: int = 600, max_entries: int = 5000) -> None:
        _validate_settings(ttl_seconds, max_entries)
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_entries = max_entries
        self._entries: dict[str, PendingRepairConfirmation] = {}
        self._lock = RLock()

    def create(
        self,
        *,
        owner_user_id: str,
        previous_response_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        action_key: str,
    ) -> PendingRepairConfirmation:
        now = datetime.now(UTC)
        entry = _new_confirmation(
            now=now,
            ttl=self.ttl,
            owner_user_id=owner_user_id,
            previous_response_id=previous_response_id,
            tool_name=tool_name,
            arguments=arguments,
            action_key=action_key,
        )
        with self._lock:
            self._purge_locked(now)
            if len(self._entries) >= self.max_entries:
                oldest_id = min(self._entries, key=lambda key: self._entries[key].created_at)
                del self._entries[oldest_id]
            self._entries[entry.id] = entry
        return entry

    def consume(self, *, confirmation_id: str, owner_user_id: str) -> PendingRepairConfirmation:
        now = datetime.now(UTC)
        with self._lock:
            entry = self._entries.get(confirmation_id)
            if entry is None or entry.owner_user_id != owner_user_id:
                raise RepairConfirmationNotFound("repair confirmation not found")
            if entry.consumed_at is not None:
                raise RepairConfirmationConsumed("repair confirmation was already used")
            if entry.expires_at <= now:
                del self._entries[confirmation_id]
                raise RepairConfirmationExpired("repair confirmation expired")
            consumed = PendingRepairConfirmation(**{**entry.__dict__, "consumed_at": now})
            self._entries[confirmation_id] = consumed
            return consumed

    def _purge_locked(self, now: datetime) -> None:
        expired = [
            key
            for key, entry in self._entries.items()
            if entry.expires_at <= now or entry.consumed_at is not None
        ]
        for key in expired:
            del self._entries[key]


class SqlRepairConfirmationStore:
    """Database-backed, one-time confirmation store safe across app workers."""

    def __init__(
        self,
        session: Session,
        *,
        ttl_seconds: int = 600,
        max_entries: int = 5000,
    ) -> None:
        _validate_settings(ttl_seconds, max_entries)
        self.session = session
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_entries = max_entries

    def create(
        self,
        *,
        owner_user_id: str,
        previous_response_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        action_key: str,
    ) -> PendingRepairConfirmation:
        now = datetime.now(UTC)
        entry = _new_confirmation(
            now=now,
            ttl=self.ttl,
            owner_user_id=owner_user_id,
            previous_response_id=previous_response_id,
            tool_name=tool_name,
            arguments=arguments,
            action_key=action_key,
        )
        try:
            self._purge(now)
            active_ids = self.session.scalars(
                select(RepairConfirmationRow.id)
                .where(RepairConfirmationRow.consumed_at.is_(None))
                .order_by(RepairConfirmationRow.created_at.asc())
            ).all()
            excess = len(active_ids) - self.max_entries + 1
            if excess > 0:
                self.session.execute(
                    delete(RepairConfirmationRow).where(
                        RepairConfirmationRow.id.in_(active_ids[:excess])
                    )
                )
            self.session.add(
                RepairConfirmationRow(
                    id=entry.id,
                    owner_user_id=entry.owner_user_id,
                    previous_response_id=entry.previous_response_id,
                    tool_name=entry.tool_name,
                    arguments_json=entry.arguments,
                    action_key=entry.action_key,
                    created_at=entry.created_at,
                    expires_at=entry.expires_at,
                    consumed_at=None,
                )
            )
            self.session.commit()
            return entry
        except Exception:
            self.session.rollback()
            raise

    def consume(self, *, confirmation_id: str, owner_user_id: str) -> PendingRepairConfirmation:
        now = datetime.now(UTC)
        row = self.session.scalar(
            select(RepairConfirmationRow).where(
                RepairConfirmationRow.id == confirmation_id,
                RepairConfirmationRow.owner_user_id == owner_user_id,
            )
        )
        if row is None:
            raise RepairConfirmationNotFound("repair confirmation not found")
        if row.consumed_at is not None:
            raise RepairConfirmationConsumed("repair confirmation was already used")
        if _as_utc(row.expires_at) <= now:
            self.session.delete(row)
            self.session.commit()
            raise RepairConfirmationExpired("repair confirmation expired")

        result = cast(
            CursorResult[Any],
            self.session.execute(
                update(RepairConfirmationRow)
                .where(
                    RepairConfirmationRow.id == confirmation_id,
                    RepairConfirmationRow.owner_user_id == owner_user_id,
                    RepairConfirmationRow.consumed_at.is_(None),
                    RepairConfirmationRow.expires_at > now,
                )
                .values(consumed_at=now)
                .execution_options(synchronize_session=False)
            ),
        )

        if result.rowcount != 1:
            self.session.rollback()
            raise RepairConfirmationConsumed("repair confirmation was already used")

        self.session.commit()
        return PendingRepairConfirmation(
            id=row.id,
            owner_user_id=row.owner_user_id,
            previous_response_id=row.previous_response_id,
            tool_name=row.tool_name,
            arguments=dict(row.arguments_json),
            action_key=row.action_key,
            created_at=_as_utc(row.created_at),
            expires_at=_as_utc(row.expires_at),
            consumed_at=now,
        )

    def _purge(self, now: datetime) -> None:
        self.session.execute(
            delete(RepairConfirmationRow).where(
                (RepairConfirmationRow.expires_at <= now)
                | (RepairConfirmationRow.consumed_at.is_not(None))
            )
        )


def _validate_settings(ttl_seconds: int, max_entries: int) -> None:
    if ttl_seconds < 30:
        raise ValueError("confirmation TTL must be at least 30 seconds")
    if max_entries < 1:
        raise ValueError("confirmation store must allow at least one entry")


def _new_confirmation(
    *,
    now: datetime,
    ttl: timedelta,
    owner_user_id: str,
    previous_response_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    action_key: str,
) -> PendingRepairConfirmation:
    return PendingRepairConfirmation(
        id=f"rcf_{uuid4().hex}",
        owner_user_id=owner_user_id,
        previous_response_id=previous_response_id,
        tool_name=tool_name,
        arguments=dict(arguments),
        action_key=action_key,
        created_at=now,
        expires_at=now + ttl,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = [
    "PendingRepairConfirmation",
    "RepairConfirmationConsumed",
    "RepairConfirmationError",
    "RepairConfirmationExpired",
    "RepairConfirmationNotFound",
    "RepairConfirmationStore",
    "SqlRepairConfirmationStore",
]

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4


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
    """Thread-safe, process-local store for one-time repair action confirmations."""

    def __init__(self, *, ttl_seconds: int = 600, max_entries: int = 5000) -> None:
        if ttl_seconds < 30:
            raise ValueError("confirmation TTL must be at least 30 seconds")
        if max_entries < 1:
            raise ValueError("confirmation store must allow at least one entry")
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
        entry = PendingRepairConfirmation(
            id=f"rcf_{uuid4().hex}",
            owner_user_id=owner_user_id,
            previous_response_id=previous_response_id,
            tool_name=tool_name,
            arguments=dict(arguments),
            action_key=action_key,
            created_at=now,
            expires_at=now + self.ttl,
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
            consumed = PendingRepairConfirmation(
                id=entry.id,
                owner_user_id=entry.owner_user_id,
                previous_response_id=entry.previous_response_id,
                tool_name=entry.tool_name,
                arguments=dict(entry.arguments),
                action_key=entry.action_key,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
                consumed_at=now,
            )
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


__all__ = [
    "PendingRepairConfirmation",
    "RepairConfirmationConsumed",
    "RepairConfirmationError",
    "RepairConfirmationExpired",
    "RepairConfirmationNotFound",
    "RepairConfirmationStore",
]

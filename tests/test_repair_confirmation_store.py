from datetime import UTC, datetime, timedelta

import pytest

from nocturnix.repair_confirmation_store import (
    RepairConfirmationConsumed,
    RepairConfirmationExpired,
    RepairConfirmationNotFound,
    RepairConfirmationStore,
)


def create_pending(store: RepairConfirmationStore, *, owner: str = "owner-1"):
    return store.create(
        owner_user_id=owner,
        previous_response_id="resp_123",
        tool_name="create_customer",
        arguments={"first_name": "Ada", "last_name": "Lovelace"},
        action_key='create_customer:{"first_name":"Ada","last_name":"Lovelace"}',
    )


def test_confirmation_is_user_bound_and_one_time() -> None:
    store = RepairConfirmationStore(ttl_seconds=600)
    pending = create_pending(store)

    with pytest.raises(RepairConfirmationNotFound):
        store.consume(confirmation_id=pending.id, owner_user_id="owner-2")

    consumed = store.consume(confirmation_id=pending.id, owner_user_id="owner-1")
    assert consumed.action_key == pending.action_key
    assert consumed.previous_response_id == "resp_123"
    assert consumed.consumed_at is not None

    with pytest.raises(RepairConfirmationConsumed):
        store.consume(confirmation_id=pending.id, owner_user_id="owner-1")


def test_expired_confirmation_cannot_be_consumed() -> None:
    store = RepairConfirmationStore(ttl_seconds=600)
    pending = create_pending(store)
    expired = pending.__class__(
        id=pending.id,
        owner_user_id=pending.owner_user_id,
        previous_response_id=pending.previous_response_id,
        tool_name=pending.tool_name,
        arguments=pending.arguments,
        action_key=pending.action_key,
        created_at=datetime.now(UTC) - timedelta(minutes=20),
        expires_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    store._entries[pending.id] = expired

    with pytest.raises(RepairConfirmationExpired):
        store.consume(confirmation_id=pending.id, owner_user_id="owner-1")


def test_store_evicts_oldest_entry_at_capacity() -> None:
    store = RepairConfirmationStore(ttl_seconds=600, max_entries=1)
    first = create_pending(store)
    second = create_pending(store)

    with pytest.raises(RepairConfirmationNotFound):
        store.consume(confirmation_id=first.id, owner_user_id="owner-1")

    assert store.consume(confirmation_id=second.id, owner_user_id="owner-1").id == second.id


def test_store_validates_bounds() -> None:
    with pytest.raises(ValueError):
        RepairConfirmationStore(ttl_seconds=29)
    with pytest.raises(ValueError):
        RepairConfirmationStore(max_entries=0)

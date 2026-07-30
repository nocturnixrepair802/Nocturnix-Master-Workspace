from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from nocturnix.db import Base
from nocturnix.repair_confirmation_store import (
    RepairConfirmationConsumed,
    RepairConfirmationExpired,
    RepairConfirmationNotFound,
    SqlRepairConfirmationStore,
)
from nocturnix.persistence.repair_models import RepairConfirmationRow


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database_session:
        yield database_session
    engine.dispose()


def create_confirmation(store: SqlRepairConfirmationStore, owner: str = "owner-1"):
    return store.create(
        owner_user_id=owner,
        previous_response_id="resp_123",
        tool_name="create_customer",
        arguments={"first_name": "Ada", "last_name": "Lovelace"},
        action_key='create_customer:{"first_name":"Ada","last_name":"Lovelace"}',
    )


def test_confirmation_persists_across_store_instances(session: Session) -> None:
    created = create_confirmation(SqlRepairConfirmationStore(session))

    restored = SqlRepairConfirmationStore(session).consume(
        confirmation_id=created.id,
        owner_user_id="owner-1",
    )

    assert restored.id == created.id
    assert restored.previous_response_id == "resp_123"
    assert restored.arguments["first_name"] == "Ada"
    assert restored.consumed_at is not None


def test_confirmation_is_bound_to_owner(session: Session) -> None:
    created = create_confirmation(SqlRepairConfirmationStore(session))

    with pytest.raises(RepairConfirmationNotFound):
        SqlRepairConfirmationStore(session).consume(
            confirmation_id=created.id,
            owner_user_id="owner-2",
        )


def test_confirmation_is_one_time(session: Session) -> None:
    store = SqlRepairConfirmationStore(session)
    created = create_confirmation(store)
    store.consume(confirmation_id=created.id, owner_user_id="owner-1")

    with pytest.raises(RepairConfirmationConsumed):
        SqlRepairConfirmationStore(session).consume(
            confirmation_id=created.id,
            owner_user_id="owner-1",
        )


def test_expired_confirmation_is_rejected_and_deleted(session: Session) -> None:
    created = create_confirmation(SqlRepairConfirmationStore(session))
    session.execute(
        update(RepairConfirmationRow)
        .where(RepairConfirmationRow.id == created.id)
        .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    session.commit()

    with pytest.raises(RepairConfirmationExpired):
        SqlRepairConfirmationStore(session).consume(
            confirmation_id=created.id,
            owner_user_id="owner-1",
        )

    assert session.get(RepairConfirmationRow, created.id) is None


def test_capacity_evicts_oldest_active_confirmation(session: Session) -> None:
    store = SqlRepairConfirmationStore(session, max_entries=1)
    first = create_confirmation(store)
    second = create_confirmation(store)

    assert session.get(RepairConfirmationRow, first.id) is None
    assert session.get(RepairConfirmationRow, second.id) is not None

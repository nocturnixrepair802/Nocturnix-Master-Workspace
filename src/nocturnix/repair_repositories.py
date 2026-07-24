from __future__ import annotations

import builtins
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from nocturnix.repair_models import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    CustomerDeviceUpdateRequest,
    CustomerUpdateRequest,
    RepairTicketCreateRequest,
    RepairTicketNoteCreateRequest,
    RepairTicketNoteUpdateRequest,
    RepairTicketStatus,
    RepairTicketUpdateRequest,
)
from nocturnix.repair_persistence_models import (
    CustomerDeviceRow,
    CustomerRow,
    RepairTicketNoteRow,
    RepairTicketRow,
    RepairTicketStatusHistoryRow,
)


class CustomerRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        request: CustomerCreateRequest,
    ) -> CustomerRow: ...

    def get(
        self,
        owner_user_id: str,
        customer_id: str,
    ) -> CustomerRow | None: ...

    def list(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[CustomerRow], int]: ...

    def update(
        self,
        owner_user_id: str,
        customer_id: str,
        request: CustomerUpdateRequest,
    ) -> CustomerRow | None: ...


class CustomerDeviceRepository(Protocol):
    def create(
        self, owner_user_id: str, request: CustomerDeviceCreateRequest
    ) -> CustomerDeviceRow: ...

    def get(self, owner_user_id: str, device_id: str) -> CustomerDeviceRow | None: ...

    def list_for_customer(
        self,
        owner_user_id: str,
        customer_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[CustomerDeviceRow], int]: ...

    def update(
        self,
        owner_user_id: str,
        device_id: str,
        request: CustomerDeviceUpdateRequest,
    ) -> CustomerDeviceRow | None: ...


class RepairTicketRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        ticket_number: str,
        request: RepairTicketCreateRequest,
    ) -> RepairTicketRow: ...

    def get(self, owner_user_id: str, ticket_id: str) -> RepairTicketRow | None: ...

    def get_by_number(self, owner_user_id: str, ticket_number: str) -> RepairTicketRow | None: ...

    def list(
        self,
        owner_user_id: str,
        *,
        customer_id: str | None = None,
        device_id: str | None = None,
        assigned_user_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[RepairTicketRow], int]: ...

    def update(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketUpdateRequest,
    ) -> RepairTicketRow | None: ...

    def change_status(
        self,
        owner_user_id: str,
        ticket_id: str,
        status: RepairTicketStatus,
        *,
        changed_by_user_id: str | None,
        reason: str | None,
    ) -> RepairTicketRow | None: ...


class RepairTicketNoteRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        ticket_id: str,
        author_user_id: str | None,
        request: RepairTicketNoteCreateRequest,
    ) -> RepairTicketNoteRow: ...

    def get(self, owner_user_id: str, note_id: str) -> RepairTicketNoteRow | None: ...

    def list_for_ticket(
        self,
        owner_user_id: str,
        ticket_id: str,
        *,
        customer_visible_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[RepairTicketNoteRow], int]: ...

    def update(
        self,
        owner_user_id: str,
        note_id: str,
        request: RepairTicketNoteUpdateRequest,
    ) -> RepairTicketNoteRow | None: ...


class SqlCustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, owner_user_id: str, request: CustomerCreateRequest) -> CustomerRow:
        now = datetime.now(UTC)
        row = CustomerRow(
            id=f"cust_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            created_at=now,
            updated_at=now,
            **request.model_dump(mode="json"),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, owner_user_id: str, customer_id: str) -> CustomerRow | None:
        return self.session.scalar(
            select(CustomerRow).where(
                CustomerRow.id == customer_id,
                CustomerRow.owner_user_id == owner_user_id,
            )
        )

    def list(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[CustomerRow], int]:
        stmt: Select[tuple[CustomerRow]] = select(CustomerRow).where(
            CustomerRow.owner_user_id == owner_user_id
        )
        if status:
            stmt = stmt.where(CustomerRow.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    CustomerRow.first_name.ilike(pattern),
                    CustomerRow.last_name.ilike(pattern),
                    CustomerRow.email.ilike(pattern),
                    CustomerRow.phone.ilike(pattern),
                    CustomerRow.company_name.ilike(pattern),
                )
            )
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.session.scalars(
            stmt.order_by(CustomerRow.last_name, CustomerRow.first_name).offset(offset).limit(limit)
        ).all()
        return list(rows), total

    def update(
        self,
        owner_user_id: str,
        customer_id: str,
        request: CustomerUpdateRequest,
    ) -> CustomerRow | None:
        row = self.get(owner_user_id, customer_id)
        if row is None:
            return None
        _apply_changes(row, request.model_dump(exclude_unset=True, mode="json"))
        row.updated_at = datetime.now(UTC)
        self.session.flush()
        return row


class SqlCustomerDeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, owner_user_id: str, request: CustomerDeviceCreateRequest) -> CustomerDeviceRow:
        now = datetime.now(UTC)
        row = CustomerDeviceRow(
            id=f"dev_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            created_at=now,
            updated_at=now,
            **request.model_dump(mode="json"),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, owner_user_id: str, device_id: str) -> CustomerDeviceRow | None:
        return self.session.scalar(
            select(CustomerDeviceRow).where(
                CustomerDeviceRow.id == device_id,
                CustomerDeviceRow.owner_user_id == owner_user_id,
            )
        )

    def list_for_customer(
        self,
        owner_user_id: str,
        customer_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[CustomerDeviceRow], int]:
        stmt = select(CustomerDeviceRow).where(
            CustomerDeviceRow.owner_user_id == owner_user_id,
            CustomerDeviceRow.customer_id == customer_id,
        )
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.session.scalars(
            stmt.order_by(CustomerDeviceRow.created_at.desc()).offset(offset).limit(limit)
        ).all()
        return list(rows), total

    def update(
        self,
        owner_user_id: str,
        device_id: str,
        request: CustomerDeviceUpdateRequest,
    ) -> CustomerDeviceRow | None:
        row = self.get(owner_user_id, device_id)
        if row is None:
            return None
        _apply_changes(row, request.model_dump(exclude_unset=True, mode="json"))
        row.updated_at = datetime.now(UTC)
        self.session.flush()
        return row


class SqlRepairTicketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        owner_user_id: str,
        ticket_number: str,
        request: RepairTicketCreateRequest,
    ) -> RepairTicketRow:
        now = datetime.now(UTC)
        row = RepairTicketRow(
            id=f"ticket_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            ticket_number=ticket_number,
            status=RepairTicketStatus.received.value,
            created_at=now,
            updated_at=now,
            completed_at=None,
            cancelled_at=None,
            **request.model_dump(mode="json"),
        )
        self.session.add(row)
        self.session.add(
            RepairTicketStatusHistoryRow(
                id=f"hist_{uuid4().hex[:16]}",
                owner_user_id=owner_user_id,
                repair_ticket_id=row.id,
                from_status=None,
                to_status=RepairTicketStatus.received.value,
                changed_by_user_id=None,
                reason="Ticket created",
                created_at=now,
            )
        )
        self.session.flush()
        return row

    def get(self, owner_user_id: str, ticket_id: str) -> RepairTicketRow | None:
        return self.session.scalar(
            select(RepairTicketRow).where(
                RepairTicketRow.id == ticket_id,
                RepairTicketRow.owner_user_id == owner_user_id,
            )
        )

    def get_by_number(self, owner_user_id: str, ticket_number: str) -> RepairTicketRow | None:
        return self.session.scalar(
            select(RepairTicketRow).where(
                RepairTicketRow.ticket_number == ticket_number,
                RepairTicketRow.owner_user_id == owner_user_id,
            )
        )

    def list(
        self,
        owner_user_id: str,
        *,
        customer_id: str | None = None,
        device_id: str | None = None,
        assigned_user_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[RepairTicketRow], int]:
        stmt: Select[tuple[RepairTicketRow]] = select(RepairTicketRow).where(
            RepairTicketRow.owner_user_id == owner_user_id
        )
        if customer_id:
            stmt = stmt.where(RepairTicketRow.customer_id == customer_id)
        if device_id:
            stmt = stmt.where(RepairTicketRow.customer_device_id == device_id)
        if assigned_user_id:
            stmt = stmt.where(RepairTicketRow.assigned_user_id == assigned_user_id)
        if status:
            stmt = stmt.where(RepairTicketRow.status == status)
        if priority:
            stmt = stmt.where(RepairTicketRow.priority == priority)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    RepairTicketRow.ticket_number.ilike(pattern),
                    RepairTicketRow.issue_description.ilike(pattern),
                    RepairTicketRow.diagnostic_summary.ilike(pattern),
                )
            )
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.session.scalars(
            stmt.order_by(RepairTicketRow.created_at.desc()).offset(offset).limit(limit)
        ).all()
        return list(rows), total

    def update(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketUpdateRequest,
    ) -> RepairTicketRow | None:
        row = self.get(owner_user_id, ticket_id)
        if row is None:
            return None
        _apply_changes(row, request.model_dump(exclude_unset=True, mode="json"))
        row.updated_at = datetime.now(UTC)
        self.session.flush()
        return row

    def change_status(
        self,
        owner_user_id: str,
        ticket_id: str,
        status: RepairTicketStatus,
        *,
        changed_by_user_id: str | None,
        reason: str | None,
    ) -> RepairTicketRow | None:
        row = self.get(owner_user_id, ticket_id)
        if row is None:
            return None
        now = datetime.now(UTC)
        previous_status = row.status
        row.status = status.value
        row.updated_at = now
        if status == RepairTicketStatus.completed:
            row.completed_at = now
            row.cancelled_at = None
        elif status == RepairTicketStatus.cancelled:
            row.cancelled_at = now
            row.completed_at = None
        self.session.add(
            RepairTicketStatusHistoryRow(
                id=f"hist_{uuid4().hex[:16]}",
                owner_user_id=owner_user_id,
                repair_ticket_id=ticket_id,
                from_status=previous_status,
                to_status=status.value,
                changed_by_user_id=changed_by_user_id,
                reason=reason,
                created_at=now,
            )
        )
        self.session.flush()
        return row

    def list_status_history(
        self,
        owner_user_id: str,
        ticket_id: str,
    ) -> builtins.list[RepairTicketStatusHistoryRow]:
        return builtins.list(
            self.session.scalars(
                select(RepairTicketStatusHistoryRow)
                .where(
                    RepairTicketStatusHistoryRow.owner_user_id == owner_user_id,
                    RepairTicketStatusHistoryRow.repair_ticket_id == ticket_id,
                )
                .order_by(RepairTicketStatusHistoryRow.created_at)
            ).all()
        )


class SqlRepairTicketNoteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        owner_user_id: str,
        ticket_id: str,
        author_user_id: str | None,
        request: RepairTicketNoteCreateRequest,
    ) -> RepairTicketNoteRow:
        now = datetime.now(UTC)
        row = RepairTicketNoteRow(
            id=f"note_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            repair_ticket_id=ticket_id,
            author_user_id=author_user_id,
            created_at=now,
            updated_at=now,
            **request.model_dump(mode="json"),
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, owner_user_id: str, note_id: str) -> RepairTicketNoteRow | None:
        return self.session.scalar(
            select(RepairTicketNoteRow).where(
                RepairTicketNoteRow.id == note_id,
                RepairTicketNoteRow.owner_user_id == owner_user_id,
            )
        )

    def list_for_ticket(
        self,
        owner_user_id: str,
        ticket_id: str,
        *,
        customer_visible_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[RepairTicketNoteRow], int]:
        stmt = select(RepairTicketNoteRow).where(
            RepairTicketNoteRow.owner_user_id == owner_user_id,
            RepairTicketNoteRow.repair_ticket_id == ticket_id,
        )
        if customer_visible_only:
            stmt = stmt.where(RepairTicketNoteRow.customer_visible.is_(True))
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.session.scalars(
            stmt.order_by(RepairTicketNoteRow.created_at).offset(offset).limit(limit)
        ).all()
        return list(rows), total

    def update(
        self,
        owner_user_id: str,
        note_id: str,
        request: RepairTicketNoteUpdateRequest,
    ) -> RepairTicketNoteRow | None:
        row = self.get(owner_user_id, note_id)
        if row is None:
            return None
        _apply_changes(row, request.model_dump(exclude_unset=True, mode="json"))
        row.updated_at = datetime.now(UTC)
        self.session.flush()
        return row


def _apply_changes(row: object, changes: Mapping[str, object]) -> None:
    for field_name, value in changes.items():
        setattr(row, field_name, value)

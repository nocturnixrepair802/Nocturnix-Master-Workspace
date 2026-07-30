from __future__ import annotations

import builtins
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from nocturnix.persistence.repair_models import (
    CustomerDeviceRow,
    CustomerRow,
    RepairPricingPolicyRow,
    RepairServiceRow,
    RepairTaxPolicyRow,
    RepairTicketLineItemRow,
    RepairTicketNoteRow,
    RepairTicketRow,
    RepairTicketStatusHistoryRow,
)
from nocturnix.repair_models import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    CustomerDeviceUpdateRequest,
    CustomerUpdateRequest,
    RepairPricingPolicyCreateRequest,
    RepairPricingPolicyUpdateRequest,
    RepairServiceCreateRequest,
    RepairServiceUpdateRequest,
    RepairTaxPolicyCreateRequest,
    RepairTaxPolicyUpdateRequest,
    RepairTicketCreateRequest,
    RepairTicketLineItemCreateRequest,
    RepairTicketLineItemUpdateRequest,
    RepairTicketNoteCreateRequest,
    RepairTicketNoteUpdateRequest,
    RepairTicketStatus,
    RepairTicketUpdateRequest,
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
    ) -> tuple[builtins.list[CustomerRow], int]: ...

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
    ) -> tuple[builtins.list[CustomerDeviceRow], int]: ...

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
    ) -> tuple[builtins.list[RepairTicketRow], int]: ...

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
    ) -> tuple[builtins.list[RepairTicketNoteRow], int]: ...

    def update(
        self,
        owner_user_id: str,
        note_id: str,
        request: RepairTicketNoteUpdateRequest,
    ) -> RepairTicketNoteRow | None: ...


class RepairTicketLineItemRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketLineItemCreateRequest,
    ) -> RepairTicketLineItemRow: ...

    def get(
        self,
        owner_user_id: str,
        line_item_id: str,
    ) -> RepairTicketLineItemRow | None: ...

    def list_for_ticket(
        self,
        owner_user_id: str,
        ticket_id: str,
    ) -> builtins.list[RepairTicketLineItemRow]: ...

    def update(
        self,
        owner_user_id: str,
        line_item_id: str,
        request: RepairTicketLineItemUpdateRequest,
    ) -> RepairTicketLineItemRow | None: ...

    def delete(
        self,
        owner_user_id: str,
        line_item_id: str,
    ) -> bool: ...


class RepairPricingPolicyRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        request: RepairPricingPolicyCreateRequest,
    ) -> RepairPricingPolicyRow: ...

    def get(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> RepairPricingPolicyRow | None: ...

    def list(
        self,
        owner_user_id: str,
    ) -> builtins.list[RepairPricingPolicyRow]: ...

    def update(
        self,
        owner_user_id: str,
        policy_id: str,
        request: RepairPricingPolicyUpdateRequest,
    ) -> RepairPricingPolicyRow | None: ...

    def delete(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> bool: ...

    def get_default(
        self,
        owner_user_id: str,
    ) -> RepairPricingPolicyRow | None: ...


class RepairServiceRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        request: RepairServiceCreateRequest,
    ) -> RepairServiceRow: ...

    def get(
        self,
        owner_user_id: str,
        service_id: str,
    ) -> RepairServiceRow | None: ...

    def list(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[RepairServiceRow], int]: ...

    def update(
        self,
        row: RepairServiceRow,
        request: RepairServiceUpdateRequest,
    ) -> RepairServiceRow: ...

    def delete(
        self,
        row: RepairServiceRow,
    ) -> None: ...


class RepairTaxPolicyRepository(Protocol):
    def create(
        self,
        owner_user_id: str,
        request: RepairTaxPolicyCreateRequest,
    ) -> RepairTaxPolicyRow: ...

    def get(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> RepairTaxPolicyRow | None: ...

    def list(
        self,
        owner_user_id: str,
    ) -> builtins.list[RepairTaxPolicyRow]: ...

    def update(
        self,
        owner_user_id: str,
        policy_id: str,
        request: RepairTaxPolicyUpdateRequest,
    ) -> RepairTaxPolicyRow | None: ...

    def delete(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> bool: ...

    def get_default(
        self,
        owner_user_id: str,
    ) -> RepairTaxPolicyRow | None: ...


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
            **request.model_dump(mode="python"),
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
    ) -> tuple[builtins.list[CustomerRow], int]:
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
            **request.model_dump(mode="python"),
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
    ) -> tuple[builtins.list[CustomerDeviceRow], int]:
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
            **request.model_dump(mode="python"),
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
    ) -> tuple[builtins.list[RepairTicketRow], int]:
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

    def count_by_status(self, owner_user_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(RepairTicketRow.status, func.count())
            .where(RepairTicketRow.owner_user_id == owner_user_id)
            .group_by(RepairTicketRow.status)
        ).all()
        return {str(status): int(count) for status, count in rows}

    def count_by_priority(self, owner_user_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(RepairTicketRow.priority, func.count())
            .where(RepairTicketRow.owner_user_id == owner_user_id)
            .group_by(RepairTicketRow.priority)
        ).all()
        return {str(priority): int(count) for priority, count in rows}

    def recent_dashboard_queue(
        self, owner_user_id: str, *, limit: int = 10
    ) -> builtins.list[tuple[RepairTicketRow, CustomerRow, CustomerDeviceRow]]:
        rows = self.session.execute(
            select(RepairTicketRow, CustomerRow, CustomerDeviceRow)
            .join(CustomerRow, RepairTicketRow.customer_id == CustomerRow.id)
            .join(CustomerDeviceRow, RepairTicketRow.customer_device_id == CustomerDeviceRow.id)
            .where(RepairTicketRow.owner_user_id == owner_user_id)
            .order_by(RepairTicketRow.updated_at.desc(), RepairTicketRow.created_at.desc())
            .limit(limit)
        ).all()
        return [(ticket, customer, device) for ticket, customer, device in rows]


def count_customers(session: Session, owner_user_id: str) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(CustomerRow)
            .where(CustomerRow.owner_user_id == owner_user_id)
        )
        or 0
    )


def count_devices(session: Session, owner_user_id: str) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(CustomerDeviceRow).where(
                CustomerDeviceRow.owner_user_id == owner_user_id
            )
        )
        or 0
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
            **request.model_dump(mode="python"),
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
    ) -> tuple[builtins.list[RepairTicketNoteRow], int]:
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


class SqlRepairTicketLineItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketLineItemCreateRequest,
    ) -> RepairTicketLineItemRow:
        now = datetime.now(UTC)

        current_max = self.session.scalar(
            select(func.max(RepairTicketLineItemRow.line_number)).where(
                RepairTicketLineItemRow.owner_user_id == owner_user_id,
                RepairTicketLineItemRow.repair_ticket_id == ticket_id,
            )
        )
        line_number = int(current_max or 0) + 1

        values = request.model_dump(mode="json")
        line_total_cents = (
            request.quantity * request.unit_price_cents
        ) - request.discount_cents

        row = RepairTicketLineItemRow(
            id=f"line_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            repair_ticket_id=ticket_id,
            line_number=line_number,
            line_total_cents=line_total_cents,
            created_at=now,
            updated_at=now,
            **values,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(
        self,
        owner_user_id: str,
        line_item_id: str,
    ) -> RepairTicketLineItemRow | None:
        return self.session.scalar(
            select(RepairTicketLineItemRow).where(
                RepairTicketLineItemRow.id == line_item_id,
                RepairTicketLineItemRow.owner_user_id == owner_user_id,
            )
        )

    def list_for_ticket(
        self,
        owner_user_id: str,
        ticket_id: str,
    ) -> builtins.list[RepairTicketLineItemRow]:
        return builtins.list(
            self.session.scalars(
                select(RepairTicketLineItemRow)
                .where(
                    RepairTicketLineItemRow.owner_user_id == owner_user_id,
                    RepairTicketLineItemRow.repair_ticket_id == ticket_id,
                )
                .order_by(RepairTicketLineItemRow.line_number)
            ).all()
        )

    def update(
        self,
        owner_user_id: str,
        line_item_id: str,
        request: RepairTicketLineItemUpdateRequest,
    ) -> RepairTicketLineItemRow | None:
        row = self.get(owner_user_id, line_item_id)
        if row is None:
            return None

        changes = request.model_dump(exclude_unset=True, mode="python")
        _apply_changes(row, changes)

        row.line_total_cents = (
            row.quantity * row.unit_price_cents
        ) - row.discount_cents
        row.updated_at = datetime.now(UTC)

        self.session.flush()
        return row

    def delete(
        self,
        owner_user_id: str,
        line_item_id: str,
    ) -> bool:
        row = self.get(owner_user_id, line_item_id)
        if row is None:
            return False

        self.session.delete(row)
        self.session.flush()
        return True


class SqlRepairPricingPolicyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        owner_user_id: str,
        request: RepairPricingPolicyCreateRequest,
    ) -> RepairPricingPolicyRow:
        now = datetime.now(UTC)

        if request.is_default:
            self._clear_default(owner_user_id)

        row = RepairPricingPolicyRow(
            id=f"price_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            created_at=now,
            updated_at=now,
            **request.model_dump(mode="python"),
        )

        self.session.add(row)
        self.session.flush()
        return row

    def get(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> RepairPricingPolicyRow | None:
        return self.session.scalar(
            select(RepairPricingPolicyRow).where(
                RepairPricingPolicyRow.id == policy_id,
                RepairPricingPolicyRow.owner_user_id == owner_user_id,
            )
        )

    def list(
        self,
        owner_user_id: str,
    ) -> builtins.list[RepairPricingPolicyRow]:
        return builtins.list(
            self.session.scalars(
                select(RepairPricingPolicyRow)
                .where(RepairPricingPolicyRow.owner_user_id == owner_user_id)
                .order_by(
                    RepairPricingPolicyRow.is_default.desc(),
                    RepairPricingPolicyRow.name,
                )
            ).all()
        )

    def update(
        self,
        owner_user_id: str,
        policy_id: str,
        request: RepairPricingPolicyUpdateRequest,
    ) -> RepairPricingPolicyRow | None:
        row = self.get(owner_user_id, policy_id)
        if row is None:
            return None

        changes = request.model_dump(exclude_unset=True, mode="python")

        if changes.get("is_default") is True:
            self._clear_default(
                owner_user_id,
                exclude_policy_id=policy_id,
            )

        _apply_changes(row, changes)
        row.updated_at = datetime.now(UTC)

        self.session.flush()
        return row

    def delete(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> bool:
        row = self.get(owner_user_id, policy_id)
        if row is None:
            return False

        self.session.delete(row)
        self.session.flush()
        return True

    def get_default(
        self,
        owner_user_id: str,
    ) -> RepairPricingPolicyRow | None:
        return self.session.scalar(
            select(RepairPricingPolicyRow).where(
                RepairPricingPolicyRow.owner_user_id == owner_user_id,
                RepairPricingPolicyRow.is_default.is_(True),
            )
        )

    def _clear_default(
        self,
        owner_user_id: str,
        *,
        exclude_policy_id: str | None = None,
    ) -> None:
        stmt = select(RepairPricingPolicyRow).where(
            RepairPricingPolicyRow.owner_user_id == owner_user_id,
            RepairPricingPolicyRow.is_default.is_(True),
        )

        if exclude_policy_id is not None:
            stmt = stmt.where(RepairPricingPolicyRow.id != exclude_policy_id)

        rows = self.session.scalars(stmt).all()

        now = datetime.now(UTC)
        for row in rows:
            row.is_default = False
            row.updated_at = now


class SqlRepairServiceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        owner_user_id: str,
        request: RepairServiceCreateRequest,
    ) -> RepairServiceRow:
        now = datetime.now(UTC)

        row = RepairServiceRow(
            id=str(uuid4()),
            owner_user_id=owner_user_id,
            name=request.name,
            category=request.category,
            description=request.description,
            default_labor_minutes=request.default_labor_minutes,
            estimated_duration_minutes=request.estimated_duration_minutes,
            taxable=request.taxable,
            is_active=request.is_active,
            created_at=now,
            updated_at=now,
        )

        self.session.add(row)
        self.session.flush()
        return row

    def get(
        self,
        owner_user_id: str,
        service_id: str,
    ) -> RepairServiceRow | None:
        statement = select(RepairServiceRow).where(
            RepairServiceRow.owner_user_id == owner_user_id,
            RepairServiceRow.id == service_id,
        )

        return self.session.scalar(statement)

    def list(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[RepairServiceRow], int]:
        filters = [RepairServiceRow.owner_user_id == owner_user_id]

        if search:
            cleaned_search = search.strip()
            if cleaned_search:
                pattern = f"%{cleaned_search}%"
                filters.append(
                    or_(
                        RepairServiceRow.name.ilike(pattern),
                        RepairServiceRow.category.ilike(pattern),
                        RepairServiceRow.description.ilike(pattern),
                    )
                )

        if category:
            cleaned_category = category.strip()
            if cleaned_category:
                filters.append(
                    func.lower(RepairServiceRow.category) == cleaned_category.lower()
                )

        if is_active is not None:
            filters.append(RepairServiceRow.is_active == is_active)

        total_statement = (
            select(func.count()).select_from(RepairServiceRow).where(*filters)
        )
        total = int(self.session.scalar(total_statement) or 0)

        statement = (
            select(RepairServiceRow)
            .where(*filters)
            .order_by(
                RepairServiceRow.category.asc(),
                RepairServiceRow.name.asc(),
                RepairServiceRow.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        rows = list(self.session.scalars(statement).all())
        return rows, total

    def update(
        self,
        row: RepairServiceRow,
        request: RepairServiceUpdateRequest,
    ) -> RepairServiceRow:
        fields = request.model_fields_set

        if "name" in fields and request.name is not None:
            row.name = request.name

        if "category" in fields and request.category is not None:
            row.category = request.category

        if "description" in fields:
            row.description = request.description

        if (
            "default_labor_minutes" in fields
            and request.default_labor_minutes is not None
        ):
            row.default_labor_minutes = request.default_labor_minutes

        if "estimated_duration_minutes" in fields:
            row.estimated_duration_minutes = request.estimated_duration_minutes

        if "taxable" in fields and request.taxable is not None:
            row.taxable = request.taxable

        if "is_active" in fields and request.is_active is not None:
            row.is_active = request.is_active

        row.updated_at = datetime.now(UTC)

        self.session.flush()
        return row

    def delete(
        self,
        row: RepairServiceRow,
    ) -> None:
        self.session.delete(row)
        self.session.flush()


class SqlRepairTaxPolicyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        owner_user_id: str,
        request: RepairTaxPolicyCreateRequest,
    ) -> RepairTaxPolicyRow:
        now = datetime.now(UTC)

        if request.is_default:
            self._clear_default(owner_user_id)

        row = RepairTaxPolicyRow(
            id=f"tax_{uuid4().hex[:16]}",
            owner_user_id=owner_user_id,
            created_at=now,
            updated_at=now,
            **request.model_dump(mode="python"),
        )

        self.session.add(row)
        self.session.flush()
        return row

    def get(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> RepairTaxPolicyRow | None:
        return self.session.scalar(
            select(RepairTaxPolicyRow).where(
                RepairTaxPolicyRow.id == policy_id,
                RepairTaxPolicyRow.owner_user_id == owner_user_id,
            )
        )

    def list(
        self,
        owner_user_id: str,
    ) -> builtins.list[RepairTaxPolicyRow]:
        return builtins.list(
            self.session.scalars(
                select(RepairTaxPolicyRow)
                .where(RepairTaxPolicyRow.owner_user_id == owner_user_id)
                .order_by(
                    RepairTaxPolicyRow.is_default.desc(),
                    RepairTaxPolicyRow.name,
                )
            ).all()
        )

    def update(
        self,
        owner_user_id: str,
        policy_id: str,
        request: RepairTaxPolicyUpdateRequest,
    ) -> RepairTaxPolicyRow | None:
        row = self.get(owner_user_id, policy_id)
        if row is None:
            return None

        changes = request.model_dump(exclude_unset=True, mode="python")

        if changes.get("is_default") is True:
            self._clear_default(owner_user_id, exclude_policy_id=policy_id)

        _apply_changes(row, changes)
        row.updated_at = datetime.now(UTC)

        self.session.flush()
        return row

    def delete(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> bool:
        row = self.get(owner_user_id, policy_id)
        if row is None:
            return False

        self.session.delete(row)
        self.session.flush()
        return True

    def get_default(
        self,
        owner_user_id: str,
    ) -> RepairTaxPolicyRow | None:
        return self.session.scalar(
            select(RepairTaxPolicyRow).where(
                RepairTaxPolicyRow.owner_user_id == owner_user_id,
                RepairTaxPolicyRow.is_default.is_(True),
            )
        )

    def _clear_default(
        self,
        owner_user_id: str,
        *,
        exclude_policy_id: str | None = None,
    ) -> None:
        stmt = select(RepairTaxPolicyRow).where(
            RepairTaxPolicyRow.owner_user_id == owner_user_id,
            RepairTaxPolicyRow.is_default.is_(True),
        )

        if exclude_policy_id is not None:
            stmt = stmt.where(RepairTaxPolicyRow.id != exclude_policy_id)

        rows = self.session.scalars(stmt).all()

        now = datetime.now(UTC)
        for row in rows:
            row.is_default = False
            row.updated_at = now


def _apply_changes(row: object, changes: Mapping[str, object]) -> None:
    for field_name, value in changes.items():
        setattr(row, field_name, value)

from __future__ import annotations

from datetime import UTC, datetime
from secrets import randbelow

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
    RepairTicketStatusChangeRequest,
    RepairTicketUpdateRequest,
)
from nocturnix.repair_persistence_models import (
    CustomerDeviceRow,
    CustomerRow,
    RepairTicketNoteRow,
    RepairTicketRow,
    RepairTicketStatusHistoryRow,
)
from nocturnix.repair_repositories import (
    SqlCustomerDeviceRepository,
    SqlCustomerRepository,
    SqlRepairTicketNoteRepository,
    SqlRepairTicketRepository,
)


class RepairDomainError(Exception):
    """Base error for expected repair-domain failures."""


class RepairResourceNotFound(RepairDomainError):
    pass


class RepairConflict(RepairDomainError):
    pass


class InvalidRepairStatusTransition(RepairConflict):
    def __init__(self, current: RepairTicketStatus, requested: RepairTicketStatus) -> None:
        super().__init__(
            f"cannot transition repair ticket from {current.value} to {requested.value}"
        )
        self.current = current
        self.requested = requested


ALLOWED_STATUS_TRANSITIONS: dict[RepairTicketStatus, frozenset[RepairTicketStatus]] = {
    RepairTicketStatus.received: frozenset(
        {RepairTicketStatus.diagnosing, RepairTicketStatus.cancelled}
    ),
    RepairTicketStatus.diagnosing: frozenset(
        {
            RepairTicketStatus.awaiting_approval,
            RepairTicketStatus.approved,
            RepairTicketStatus.cancelled,
        }
    ),
    RepairTicketStatus.awaiting_approval: frozenset(
        {
            RepairTicketStatus.approved,
            RepairTicketStatus.diagnosing,
            RepairTicketStatus.cancelled,
        }
    ),
    RepairTicketStatus.approved: frozenset(
        {
            RepairTicketStatus.parts_ordered,
            RepairTicketStatus.in_repair,
            RepairTicketStatus.cancelled,
        }
    ),
    RepairTicketStatus.parts_ordered: frozenset(
        {RepairTicketStatus.in_repair, RepairTicketStatus.cancelled}
    ),
    RepairTicketStatus.in_repair: frozenset(
        {
            RepairTicketStatus.quality_check,
            RepairTicketStatus.parts_ordered,
            RepairTicketStatus.cancelled,
        }
    ),
    RepairTicketStatus.quality_check: frozenset(
        {RepairTicketStatus.in_repair, RepairTicketStatus.ready_for_pickup}
    ),
    RepairTicketStatus.ready_for_pickup: frozenset(
        {RepairTicketStatus.completed, RepairTicketStatus.in_repair}
    ),
    RepairTicketStatus.completed: frozenset(),
    RepairTicketStatus.cancelled: frozenset(),
}


class RepairService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.customers = SqlCustomerRepository(session)
        self.devices = SqlCustomerDeviceRepository(session)
        self.tickets = SqlRepairTicketRepository(session)
        self.notes = SqlRepairTicketNoteRepository(session)

    def create_customer(self, owner_user_id: str, request: CustomerCreateRequest) -> CustomerRow:
        try:
            row = self.customers.create(owner_user_id, request)
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def get_customer(self, owner_user_id: str, customer_id: str) -> CustomerRow:
        row = self.customers.get(owner_user_id, customer_id)
        if row is None:
            raise RepairResourceNotFound("customer not found")
        return row

    def list_customers(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[CustomerRow], int]:
        return self.customers.list(
            owner_user_id,
            search=search,
            status=status,
            offset=offset,
            limit=limit,
        )

    def update_customer(
        self,
        owner_user_id: str,
        customer_id: str,
        request: CustomerUpdateRequest,
    ) -> CustomerRow:
        existing = self.get_customer(owner_user_id, customer_id)
        changes = request.model_dump(exclude_unset=True)
        preferred = changes.get("preferred_contact_method", existing.preferred_contact_method)
        email = changes.get("email", existing.email)
        phone = changes.get("phone", existing.phone)
        preferred_value = getattr(preferred, "value", preferred)
        if preferred_value == "email" and not email:
            raise RepairConflict("email is required for email contact")
        if preferred_value in {"phone", "text"} and not phone:
            raise RepairConflict("phone is required for phone or text contact")
        try:
            row = self.customers.update(owner_user_id, customer_id, request)
            if row is None:
                raise RepairResourceNotFound("customer not found")
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def create_device(
        self, owner_user_id: str, request: CustomerDeviceCreateRequest
    ) -> CustomerDeviceRow:
        self.get_customer(owner_user_id, request.customer_id)
        try:
            row = self.devices.create(owner_user_id, request)
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def get_device(self, owner_user_id: str, device_id: str) -> CustomerDeviceRow:
        row = self.devices.get(owner_user_id, device_id)
        if row is None:
            raise RepairResourceNotFound("device not found")
        return row

    def list_devices(
        self,
        owner_user_id: str,
        customer_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[CustomerDeviceRow], int]:
        self.get_customer(owner_user_id, customer_id)
        return self.devices.list_for_customer(
            owner_user_id, customer_id, offset=offset, limit=limit
        )

    def update_device(
        self,
        owner_user_id: str,
        device_id: str,
        request: CustomerDeviceUpdateRequest,
    ) -> CustomerDeviceRow:
        self.get_device(owner_user_id, device_id)
        try:
            row = self.devices.update(owner_user_id, device_id, request)
            if row is None:
                raise RepairResourceNotFound("device not found")
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def create_ticket(
        self,
        owner_user_id: str,
        request: RepairTicketCreateRequest,
    ) -> RepairTicketRow:
        customer = self.get_customer(owner_user_id, request.customer_id)
        device = self.get_device(owner_user_id, request.customer_device_id)
        if device.customer_id != customer.id:
            raise RepairConflict("device does not belong to the selected customer")
        ticket_number = self._generate_ticket_number(owner_user_id)
        try:
            row = self.tickets.create(owner_user_id, ticket_number, request)
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def get_ticket(self, owner_user_id: str, ticket_id: str) -> RepairTicketRow:
        row = self.tickets.get(owner_user_id, ticket_id)
        if row is None:
            raise RepairResourceNotFound("repair ticket not found")
        return row

    def list_tickets(
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
        return self.tickets.list(
            owner_user_id,
            customer_id=customer_id,
            device_id=device_id,
            assigned_user_id=assigned_user_id,
            status=status,
            priority=priority,
            search=search,
            offset=offset,
            limit=limit,
        )

    def update_ticket(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketUpdateRequest,
    ) -> RepairTicketRow:
        current = self.get_ticket(owner_user_id, ticket_id)
        estimated = (
            request.estimated_cost_cents
            if "estimated_cost_cents" in request.model_fields_set
            else current.estimated_cost_cents
        )
        approved = (
            request.approved_cost_cents
            if "approved_cost_cents" in request.model_fields_set
            else current.approved_cost_cents
        )
        if estimated is not None and approved is not None and approved > estimated:
            raise RepairConflict("approved cost cannot exceed estimated cost")
        try:
            row = self.tickets.update(owner_user_id, ticket_id, request)
            if row is None:
                raise RepairResourceNotFound("repair ticket not found")
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def change_ticket_status(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketStatusChangeRequest,
        *,
        changed_by_user_id: str | None,
    ) -> RepairTicketRow:
        current_row = self.get_ticket(owner_user_id, ticket_id)
        current = RepairTicketStatus(current_row.status)
        requested = request.status
        if requested == current:
            raise RepairConflict("repair ticket is already in the requested status")
        if requested not in ALLOWED_STATUS_TRANSITIONS[current]:
            raise InvalidRepairStatusTransition(current, requested)
        if requested == RepairTicketStatus.approved and current_row.approved_cost_cents is None:
            raise RepairConflict("approved cost is required before approval")
        try:
            row = self.tickets.change_status(
                owner_user_id,
                ticket_id,
                requested,
                changed_by_user_id=changed_by_user_id,
                reason=request.reason,
            )
            if row is None:
                raise RepairResourceNotFound("repair ticket not found")
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def list_ticket_status_history(
        self, owner_user_id: str, ticket_id: str
    ) -> list[RepairTicketStatusHistoryRow]:
        self.get_ticket(owner_user_id, ticket_id)
        return self.tickets.list_status_history(owner_user_id, ticket_id)

    def create_ticket_note(
        self,
        owner_user_id: str,
        ticket_id: str,
        author_user_id: str | None,
        request: RepairTicketNoteCreateRequest,
    ) -> RepairTicketNoteRow:
        self.get_ticket(owner_user_id, ticket_id)
        try:
            row = self.notes.create(owner_user_id, ticket_id, author_user_id, request)
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def list_ticket_notes(
        self,
        owner_user_id: str,
        ticket_id: str,
        *,
        customer_visible_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[RepairTicketNoteRow], int]:
        self.get_ticket(owner_user_id, ticket_id)
        return self.notes.list_for_ticket(
            owner_user_id,
            ticket_id,
            customer_visible_only=customer_visible_only,
            offset=offset,
            limit=limit,
        )

    def update_ticket_note(
        self,
        owner_user_id: str,
        note_id: str,
        request: RepairTicketNoteUpdateRequest,
    ) -> RepairTicketNoteRow:
        current = self.notes.get(owner_user_id, note_id)
        if current is None:
            raise RepairResourceNotFound("repair ticket note not found")
        note_type = request.note_type.value if request.note_type else current.note_type
        visible = (
            request.customer_visible
            if "customer_visible" in request.model_fields_set
            else current.customer_visible
        )
        if note_type == "internal" and visible:
            raise RepairConflict("internal notes cannot be customer visible")
        try:
            row = self.notes.update(owner_user_id, note_id, request)
            if row is None:
                raise RepairResourceNotFound("repair ticket note not found")
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def _generate_ticket_number(self, owner_user_id: str) -> str:
        date_part = datetime.now(UTC).strftime("%Y%m%d")
        for _ in range(20):
            candidate = f"NR-{date_part}-{randbelow(1_000_000):06d}"
            if self.tickets.get_by_number(owner_user_id, candidate) is None:
                return candidate
        raise RepairConflict("unable to generate a unique ticket number")

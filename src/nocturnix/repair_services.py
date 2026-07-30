from __future__ import annotations

from datetime import UTC, datetime
from secrets import randbelow

from sqlalchemy.orm import Session

from nocturnix.persistence.repair_models import (
    CustomerDeviceRow,
    CustomerRow,
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
    RepairDashboardQueueItem,
    RepairDashboardResponse,
    RepairDashboardSummary,
    RepairPricingPolicyCreateRequest,
    RepairPricingPolicyListResponse,
    RepairPricingPolicyResponse,
    RepairPricingPolicyUpdateRequest,
    RepairPriority,
    RepairServiceCreateRequest,
    RepairServiceListResponse,
    RepairServiceResponse,
    RepairServiceUpdateRequest,
    RepairTaxPolicyCreateRequest,
    RepairTaxPolicyListResponse,
    RepairTaxPolicyResponse,
    RepairTaxPolicyUpdateRequest,
    RepairTicketCreateRequest,
    RepairTicketFinancialSummaryResponse,
    RepairTicketLineItemCreateRequest,
    RepairTicketLineItemUpdateRequest,
    RepairTicketNoteCreateRequest,
    RepairTicketNoteUpdateRequest,
    RepairTicketStatus,
    RepairTicketStatusChangeRequest,
    RepairTicketUpdateRequest,
)
from nocturnix.repair_pricing_engine import calculate_repair_pricing
from nocturnix.repair_pricing_models import (
    RepairPolicyPricingRequest,
    RepairPricingRequest,
    RepairPricingResponse,
)
from nocturnix.repair_repositories import (
    SqlCustomerDeviceRepository,
    SqlCustomerRepository,
    SqlRepairPricingPolicyRepository,
    SqlRepairServiceRepository,
    SqlRepairTaxPolicyRepository,
    SqlRepairTicketLineItemRepository,
    SqlRepairTicketNoteRepository,
    SqlRepairTicketRepository,
    count_customers,
    count_devices,
)


class RepairDomainError(Exception):
    pass


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
        self.line_items = SqlRepairTicketLineItemRepository(session)
        self.service_catalog = SqlRepairServiceRepository(session)
        self.pricing_policies = SqlRepairPricingPolicyRepository(session)
        self.tax_policies = SqlRepairTaxPolicyRepository(session)

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

    def repair_dashboard(self, owner_user_id: str) -> RepairDashboardResponse:
        status_counts = self.tickets.count_by_status(owner_user_id)
        priority_counts = self.tickets.count_by_priority(owner_user_id)
        by_status = {status: status_counts.get(status.value, 0) for status in RepairTicketStatus}
        by_priority = {
            priority: priority_counts.get(priority.value, 0) for priority in RepairPriority
        }
        terminal_statuses = {RepairTicketStatus.completed, RepairTicketStatus.cancelled}
        recent_queue = []
        for ticket, customer, device in self.tickets.recent_dashboard_queue(owner_user_id):
            manufacturer = device.manufacturer or ""
            model = device.model or device.device_type
            device_label = " ".join(part for part in [manufacturer, model] if part).strip()
            recent_queue.append(
                RepairDashboardQueueItem(
                    id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    status=RepairTicketStatus(ticket.status),
                    priority=RepairPriority(ticket.priority),
                    issue_description=ticket.issue_description,
                    customer_name=f"{customer.first_name} {customer.last_name}".strip(),
                    device_label=device_label or device.device_type,
                    estimated_cost_cents=ticket.estimated_cost_cents,
                    approved_cost_cents=ticket.approved_cost_cents,
                    currency=ticket.currency,
                    due_at=ticket.due_at,
                    updated_at=ticket.updated_at,
                )
            )
        total_tickets = sum(by_status.values())
        return RepairDashboardResponse(
            summary=RepairDashboardSummary(
                total_customers=count_customers(self.session, owner_user_id),
                total_devices=count_devices(self.session, owner_user_id),
                total_tickets=total_tickets,
                open_tickets=sum(
                    count for status, count in by_status.items() if status not in terminal_statuses
                ),
                urgent_tickets=by_priority[RepairPriority.urgent],
                awaiting_approval=by_status[RepairTicketStatus.awaiting_approval],
                ready_for_pickup=by_status[RepairTicketStatus.ready_for_pickup],
                completed_tickets=by_status[RepairTicketStatus.completed],
            ),
            tickets_by_status=by_status,
            tickets_by_priority=by_priority,
            recent_queue=recent_queue,
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

    def create_ticket_line_item(
        self,
        owner_user_id: str,
        ticket_id: str,
        request: RepairTicketLineItemCreateRequest,
    ) -> RepairTicketLineItemRow:
        ticket = self.get_ticket(owner_user_id, ticket_id)

        if request.currency != ticket.currency:
            raise RepairConflict("line item currency must match the repair ticket currency")

        try:
            row = self.line_items.create(owner_user_id, ticket_id, request)
            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def get_ticket_line_item(
        self,
        owner_user_id: str,
        line_item_id: str,
    ) -> RepairTicketLineItemRow:
        row = self.line_items.get(owner_user_id, line_item_id)
        if row is None:
            raise RepairResourceNotFound("repair ticket line item not found")
        return row

    def list_ticket_line_items(
        self,
        owner_user_id: str,
        ticket_id: str,
    ) -> list[RepairTicketLineItemRow]:
        self.get_ticket(owner_user_id, ticket_id)
        return self.line_items.list_for_ticket(owner_user_id, ticket_id)

    def get_ticket_financial_summary(
        self,
        owner_user_id: str,
        ticket_id: str,
    ) -> RepairTicketFinancialSummaryResponse:
        ticket = self.get_ticket(owner_user_id, ticket_id)
        line_items = self.line_items.list_for_ticket(owner_user_id, ticket_id)

        gross_subtotal_cents = sum(item.quantity * item.unit_price_cents for item in line_items)
        discount_total_cents = sum(item.discount_cents for item in line_items)
        net_subtotal_cents = sum(item.line_total_cents for item in line_items)
        taxable_subtotal_cents = sum(item.line_total_cents for item in line_items if item.taxable)
        non_taxable_subtotal_cents = sum(
            item.line_total_cents for item in line_items if not item.taxable
        )

        return RepairTicketFinancialSummaryResponse(
            repair_ticket_id=ticket.id,
            currency=ticket.currency,
            line_item_count=len(line_items),
            gross_subtotal_cents=gross_subtotal_cents,
            discount_total_cents=discount_total_cents,
            net_subtotal_cents=net_subtotal_cents,
            taxable_subtotal_cents=taxable_subtotal_cents,
            non_taxable_subtotal_cents=non_taxable_subtotal_cents,
        )

    def update_ticket_line_item(
        self,
        owner_user_id: str,
        line_item_id: str,
        request: RepairTicketLineItemUpdateRequest,
    ) -> RepairTicketLineItemRow:
        current = self.get_ticket_line_item(owner_user_id, line_item_id)
        ticket = self.get_ticket(owner_user_id, current.repair_ticket_id)

        quantity = request.quantity if request.quantity is not None else current.quantity
        unit_price_cents = (
            request.unit_price_cents
            if request.unit_price_cents is not None
            else current.unit_price_cents
        )
        discount_cents = (
            request.discount_cents if request.discount_cents is not None else current.discount_cents
        )
        currency = request.currency if request.currency is not None else current.currency

        gross_total = quantity * unit_price_cents

        if discount_cents > gross_total:
            raise RepairConflict("discount cannot exceed the gross line total")

        if currency != ticket.currency:
            raise RepairConflict("line item currency must match the repair ticket currency")

        try:
            row = self.line_items.update(
                owner_user_id,
                line_item_id,
                request,
            )
            if row is None:
                raise RepairResourceNotFound("repair ticket line item not found")

            self.session.commit()
            self.session.refresh(row)
            return row
        except Exception:
            self.session.rollback()
            raise

    def delete_ticket_line_item(
        self,
        owner_user_id: str,
        line_item_id: str,
    ) -> None:
        self.get_ticket_line_item(owner_user_id, line_item_id)

        try:
            deleted = self.line_items.delete(owner_user_id, line_item_id)
            if not deleted:
                raise RepairResourceNotFound("repair ticket line item not found")

            self.session.commit()
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

    def create_service(
        self,
        owner_user_id: str,
        request: RepairServiceCreateRequest,
    ) -> RepairServiceResponse:
        try:
            row = self.service_catalog.create(
                owner_user_id,
                request,
            )
            self.session.commit()
            self.session.refresh(row)
            return RepairServiceResponse.model_validate(row)
        except Exception:
            self.session.rollback()
            raise

    def get_service(
        self,
        owner_user_id: str,
        service_id: str,
    ) -> RepairServiceResponse:
        row = self.service_catalog.get(
            owner_user_id,
            service_id,
        )

        if row is None:
            raise RepairResourceNotFound("repair service not found")

        return RepairServiceResponse.model_validate(row)

    def list_services(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> RepairServiceListResponse:
        rows, total = self.service_catalog.list(
            owner_user_id,
            search=search,
            category=category,
            is_active=is_active,
            offset=offset,
            limit=limit,
        )

        return RepairServiceListResponse(
            items=[RepairServiceResponse.model_validate(row) for row in rows],
            total=total,
            offset=offset,
            limit=limit,
        )

    def update_service(
        self,
        owner_user_id: str,
        service_id: str,
        request: RepairServiceUpdateRequest,
    ) -> RepairServiceResponse:
        row = self.service_catalog.get(
            owner_user_id,
            service_id,
        )

        if row is None:
            raise RepairResourceNotFound("repair service not found")

        try:
            updated_row = self.service_catalog.update(
                row,
                request,
            )
            self.session.commit()
            self.session.refresh(updated_row)
            return RepairServiceResponse.model_validate(updated_row)
        except Exception:
            self.session.rollback()
            raise

    def delete_service(
        self,
        owner_user_id: str,
        service_id: str,
    ) -> None:
        row = self.service_catalog.get(
            owner_user_id,
            service_id,
        )

        if row is None:
            raise RepairResourceNotFound("repair service not found")

        try:
            self.service_catalog.delete(row)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def create_pricing_policy(
        self,
        owner_user_id: str,
        request: RepairPricingPolicyCreateRequest,
    ) -> RepairPricingPolicyResponse:
        try:
            row = self.pricing_policies.create(owner_user_id, request)
            self.session.commit()
            self.session.refresh(row)
            return RepairPricingPolicyResponse.model_validate(row)
        except Exception:
            self.session.rollback()
            raise

    def get_pricing_policy(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> RepairPricingPolicyResponse:
        row = self.pricing_policies.get(owner_user_id, policy_id)
        if row is None:
            raise RepairResourceNotFound("repair pricing policy not found")

        return RepairPricingPolicyResponse.model_validate(row)

    def list_pricing_policies(
        self,
        owner_user_id: str,
    ) -> RepairPricingPolicyListResponse:
        rows = self.pricing_policies.list(owner_user_id)

        return RepairPricingPolicyListResponse(
            items=[RepairPricingPolicyResponse.model_validate(row) for row in rows],
            total=len(rows),
        )

    def update_pricing_policy(
        self,
        owner_user_id: str,
        policy_id: str,
        request: RepairPricingPolicyUpdateRequest,
    ) -> RepairPricingPolicyResponse:
        try:
            row = self.pricing_policies.update(
                owner_user_id,
                policy_id,
                request,
            )
            if row is None:
                raise RepairResourceNotFound("repair pricing policy not found")

            self.session.commit()
            self.session.refresh(row)
            return RepairPricingPolicyResponse.model_validate(row)
        except Exception:
            self.session.rollback()
            raise

    def delete_pricing_policy(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> None:
        try:
            deleted = self.pricing_policies.delete(
                owner_user_id,
                policy_id,
            )
            if not deleted:
                raise RepairResourceNotFound("repair pricing policy not found")

            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def get_default_pricing_policy(
        self,
        owner_user_id: str,
    ) -> RepairPricingPolicyResponse:
        row = self.pricing_policies.get_default(owner_user_id)
        if row is None:
            raise RepairResourceNotFound("default repair pricing policy not found")

        return RepairPricingPolicyResponse.model_validate(row)

    def create_tax_policy(
        self,
        owner_user_id: str,
        request: RepairTaxPolicyCreateRequest,
    ) -> RepairTaxPolicyResponse:
        try:
            row = self.tax_policies.create(owner_user_id, request)
            self.session.commit()
            self.session.refresh(row)
            return RepairTaxPolicyResponse.model_validate(row)
        except Exception:
            self.session.rollback()
            raise

    def get_tax_policy(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> RepairTaxPolicyResponse:
        row = self.tax_policies.get(owner_user_id, policy_id)
        if row is None:
            raise RepairResourceNotFound("repair tax policy not found")

        return RepairTaxPolicyResponse.model_validate(row)

    def list_tax_policies(
        self,
        owner_user_id: str,
    ) -> RepairTaxPolicyListResponse:
        rows = self.tax_policies.list(owner_user_id)

        return RepairTaxPolicyListResponse(
            items=[RepairTaxPolicyResponse.model_validate(row) for row in rows],
            total=len(rows),
        )

    def update_tax_policy(
        self,
        owner_user_id: str,
        policy_id: str,
        request: RepairTaxPolicyUpdateRequest,
    ) -> RepairTaxPolicyResponse:
        try:
            row = self.tax_policies.update(
                owner_user_id,
                policy_id,
                request,
            )
            if row is None:
                raise RepairResourceNotFound("repair tax policy not found")

            self.session.commit()
            self.session.refresh(row)
            return RepairTaxPolicyResponse.model_validate(row)
        except Exception:
            self.session.rollback()
            raise

    def delete_tax_policy(
        self,
        owner_user_id: str,
        policy_id: str,
    ) -> None:
        try:
            deleted = self.tax_policies.delete(owner_user_id, policy_id)
            if not deleted:
                raise RepairResourceNotFound("repair tax policy not found")

            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def get_default_tax_policy(
        self,
        owner_user_id: str,
    ) -> RepairTaxPolicyResponse:
        row = self.tax_policies.get_default(owner_user_id)
        if row is None:
            raise RepairResourceNotFound("default repair tax policy not found")

        return RepairTaxPolicyResponse.model_validate(row)

    def calculate_pricing(
        self,
        owner_user_id: str,
        request: RepairPolicyPricingRequest,
    ) -> RepairPricingResponse:
        """Calculate pricing using the owner's default pricing and tax policies."""

        pricing_policy = self.get_default_pricing_policy(owner_user_id)
        tax_policy = self.get_default_tax_policy(owner_user_id)

        labor_cost_cents = (
            request.labor_minutes * pricing_policy.labor_rate_cents_per_hour + 30
        ) // 60

        direct_cost_cents = request.parts_cost_cents + labor_cost_cents

        overhead_cents = (
            direct_cost_cents * pricing_policy.overhead_basis_points + 5_000
        ) // 10_000

        calculation_request = RepairPricingRequest(
            parts_cost_cents=request.parts_cost_cents,
            labor_cost_cents=labor_cost_cents,
            processing_fee_cents=pricing_policy.processing_fee_cents,
            overhead_cents=overhead_cents,
            markup_basis_points=pricing_policy.markup_basis_points,
            tax_rate_basis_points=tax_policy.tax_rate_basis_points,
        )

        return calculate_repair_pricing(calculation_request)

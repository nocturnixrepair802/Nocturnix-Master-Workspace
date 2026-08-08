from __future__ import annotations

from nocturnix.assistant.web_models import (
    AssistantRepairTicketContextResponse,
    AssistantRepairTicketListResponse,
    AssistantRepairTicketSummary,
)
from nocturnix.repair_models import (
    CustomerDeviceResponse,
    CustomerResponse,
    RepairPriority,
    RepairTicketFinancialSummaryResponse,
    RepairTicketLineItemResponse,
    RepairTicketNoteResponse,
    RepairTicketResponse,
    RepairTicketStatus,
    RepairTicketStatusHistoryResponse,
)
from nocturnix.repair_services import RepairService

_TERMINAL_STATUSES = {
    RepairTicketStatus.completed,
    RepairTicketStatus.cancelled,
}

_OPEN_STATUSES = tuple(status for status in RepairTicketStatus if status not in _TERMINAL_STATUSES)


class AssistantRepairContextService:
    """Provide read-only repair-domain context to the Assistant."""

    def __init__(
        self,
        repair_service: RepairService,
    ) -> None:
        self._repair_service = repair_service

    def get_ticket_context(
        self,
        owner_user_id: str,
        ticket_id: str,
    ) -> AssistantRepairTicketContextResponse:
        ticket = self._repair_service.get_ticket(
            owner_user_id,
            ticket_id,
        )

        customer = self._repair_service.get_customer(
            owner_user_id,
            ticket.customer_id,
        )

        device = self._repair_service.get_device(
            owner_user_id,
            ticket.customer_device_id,
        )

        notes, _ = self._repair_service.list_ticket_notes(
            owner_user_id,
            ticket.id,
            offset=0,
            limit=100,
        )

        status_history = self._repair_service.list_ticket_status_history(
            owner_user_id,
            ticket.id,
        )

        line_items = self._repair_service.list_ticket_line_items(
            owner_user_id,
            ticket.id,
        )

        financial_summary = self._repair_service.get_ticket_financial_summary(
            owner_user_id,
            ticket.id,
        )

        return AssistantRepairTicketContextResponse(
            ticket=RepairTicketResponse.model_validate(ticket),
            customer=CustomerResponse.model_validate(customer),
            device=CustomerDeviceResponse.model_validate(device),
            notes=[RepairTicketNoteResponse.model_validate(note) for note in notes],
            status_history=[
                RepairTicketStatusHistoryResponse.model_validate(history)
                for history in status_history
            ],
            line_items=[
                RepairTicketLineItemResponse.model_validate(line_item) for line_item in line_items
            ],
            financial_summary=(
                RepairTicketFinancialSummaryResponse.model_validate(financial_summary)
            ),
        )

    def list_ticket_context(
        self,
        owner_user_id: str,
        *,
        status: RepairTicketStatus | None = None,
        limit: int = 20,
    ) -> AssistantRepairTicketListResponse:
        normalized_limit = max(
            1,
            min(limit, 100),
        )

        if status is not None:
            tickets, _ = self._repair_service.list_tickets(
                owner_user_id,
                status=status.value,
                offset=0,
                limit=normalized_limit,
            )
        else:
            tickets = []

            for open_status in _OPEN_STATUSES:
                status_tickets, _ = self._repair_service.list_tickets(
                    owner_user_id,
                    status=open_status.value,
                    offset=0,
                    limit=normalized_limit,
                )

                tickets.extend(status_tickets)

            tickets.sort(
                key=lambda ticket: (
                    ticket.updated_at,
                    ticket.created_at,
                    ticket.id,
                ),
                reverse=True,
            )

            tickets = tickets[:normalized_limit]

        items: list[AssistantRepairTicketSummary] = []

        for ticket in tickets:
            customer = self._repair_service.get_customer(
                owner_user_id,
                ticket.customer_id,
            )

            device = self._repair_service.get_device(
                owner_user_id,
                ticket.customer_device_id,
            )

            customer_name = (f"{customer.first_name} {customer.last_name}").strip()

            device_label = self._device_label(
                device.manufacturer,
                device.model,
                device.device_type,
            )

            items.append(
                AssistantRepairTicketSummary(
                    id=ticket.id,
                    ticket_number=ticket.ticket_number,
                    status=RepairTicketStatus(ticket.status),
                    priority=RepairPriority(ticket.priority),
                    issue_description=(ticket.issue_description),
                    diagnostic_summary=(ticket.diagnostic_summary),
                    customer_id=customer.id,
                    customer_name=customer_name,
                    device_id=device.id,
                    device_label=device_label,
                    estimated_cost_cents=(ticket.estimated_cost_cents),
                    approved_cost_cents=(ticket.approved_cost_cents),
                    currency=ticket.currency,
                    due_at=ticket.due_at,
                    updated_at=ticket.updated_at,
                )
            )

        return AssistantRepairTicketListResponse(
            items=items,
            total=len(items),
        )

    @staticmethod
    def _device_label(
        manufacturer: str | None,
        model: str | None,
        device_type: str,
    ) -> str:
        parts = [
            value.strip()
            for value in (
                manufacturer,
                model,
            )
            if value is not None and value.strip()
        ]

        if parts:
            return " ".join(parts)

        return device_type

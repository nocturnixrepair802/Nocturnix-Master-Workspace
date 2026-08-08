from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from nocturnix.repair_models import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    RepairTicketCreateRequest,
    RepairTicketNoteCreateRequest,
    RepairTicketStatusChangeRequest,
)


class RepairToolConfirmationRequired(Exception):
    """Raised when an AI attempts a state-changing repair action without confirmation."""


class RepairToolNotFound(Exception):
    """Raised when an unknown repair tool name is requested."""


class EmptyToolInput(BaseModel):
    pass


class CustomerLookupInput(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)


class CustomerSearchInput(BaseModel):
    search: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, max_length=40)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class CustomerDeviceListInput(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class RepairTicketLookupInput(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=64)


class RepairTicketSearchInput(BaseModel):
    customer_id: str | None = Field(default=None, max_length=64)
    device_id: str | None = Field(default=None, max_length=64)
    assigned_user_id: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=40)
    priority: str | None = Field(default=None, max_length=40)
    search: str | None = Field(default=None, max_length=200)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class RepairTicketStatusInput(RepairTicketStatusChangeRequest):
    ticket_id: str = Field(min_length=1, max_length=64)


class RepairTicketNoteInput(RepairTicketNoteCreateRequest):
    ticket_id: str = Field(min_length=1, max_length=64)


@dataclass(frozen=True)
class RepairToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    requires_confirmation: bool

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.input_model.model_json_schema(),
            "strict": False,
        }


REPAIR_TOOL_DEFINITIONS = (
    RepairToolDefinition(
        "search_customers",
        "Search the authenticated user's repair customers by name, contact details, or status.",
        CustomerSearchInput,
        False,
    ),
    RepairToolDefinition(
        "get_customer",
        "Retrieve one repair customer by ID.",
        CustomerLookupInput,
        False,
    ),
    RepairToolDefinition(
        "create_customer",
        "Create a repair customer after the user confirms the details.",
        CustomerCreateRequest,
        True,
    ),
    RepairToolDefinition(
        "list_customer_devices",
        "List devices registered to a repair customer.",
        CustomerDeviceListInput,
        False,
    ),
    RepairToolDefinition(
        "register_customer_device",
        "Register a device to an existing customer after confirmation.",
        CustomerDeviceCreateRequest,
        True,
    ),
    RepairToolDefinition(
        "search_repair_tickets",
        (
            "Search repair tickets using customer, device, status, "
            "priority, assignee, or text filters."
        ),
        RepairTicketSearchInput,
        False,
    ),
    RepairToolDefinition(
        "get_repair_ticket",
        "Retrieve a repair ticket by ID.",
        RepairTicketLookupInput,
        False,
    ),
    RepairToolDefinition(
        "create_repair_ticket",
        "Create a repair ticket for a registered customer device after confirmation.",
        RepairTicketCreateRequest,
        True,
    ),
    RepairToolDefinition(
        "update_repair_status",
        "Move a repair ticket to a valid next status after confirmation.",
        RepairTicketStatusInput,
        True,
    ),
    RepairToolDefinition(
        "get_repair_status_history",
        "Retrieve the status-change history for a repair ticket.",
        RepairTicketLookupInput,
        False,
    ),
    RepairToolDefinition(
        "add_repair_note",
        "Add an internal or customer-visible repair note after confirmation.",
        RepairTicketNoteInput,
        True,
    ),
)


class RepairAssistantTools:
    """Provider-neutral dispatcher for AI repair-management function calls."""

    def __init__(self, repair_service: Any) -> None:
        self.repair_service = repair_service
        self._definitions = {item.name: item for item in REPAIR_TOOL_DEFINITIONS}
        self._handlers: dict[str, Callable[[str, BaseModel], Any]] = {
            "search_customers": self._search_customers,
            "get_customer": self._get_customer,
            "create_customer": self._create_customer,
            "list_customer_devices": self._list_customer_devices,
            "register_customer_device": self._register_customer_device,
            "search_repair_tickets": self._search_repair_tickets,
            "get_repair_ticket": self._get_repair_ticket,
            "create_repair_ticket": self._create_repair_ticket,
            "update_repair_status": self._update_repair_status,
            "get_repair_status_history": self._get_repair_status_history,
            "add_repair_note": self._add_repair_note,
        }

    def openai_tools(self) -> list[dict[str, Any]]:
        return [definition.as_openai_tool() for definition in REPAIR_TOOL_DEFINITIONS]

    def execute(
        self,
        *,
        owner_user_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        confirmed: bool = False,
    ) -> Any:
        definition = self._definitions.get(tool_name)
        handler = self._handlers.get(tool_name)
        if definition is None or handler is None:
            raise RepairToolNotFound(f"unknown repair tool: {tool_name}")
        if definition.requires_confirmation and not confirmed:
            raise RepairToolConfirmationRequired(
                f"{tool_name} requires explicit user confirmation before execution"
            )
        validated = definition.input_model.model_validate(arguments)
        return jsonable_encoder(handler(owner_user_id, validated))

    def _search_customers(self, owner_user_id: str, model: BaseModel) -> Any:
        req = CustomerSearchInput.model_validate(model)
        items, total = self.repair_service.list_customers(owner_user_id, **req.model_dump())
        return {"items": items, "total": total, "offset": req.offset, "limit": req.limit}

    def _get_customer(self, owner_user_id: str, model: BaseModel) -> Any:
        req = CustomerLookupInput.model_validate(model)
        return self.repair_service.get_customer(owner_user_id, req.customer_id)

    def _create_customer(self, owner_user_id: str, model: BaseModel) -> Any:
        return self.repair_service.create_customer(
            owner_user_id, CustomerCreateRequest.model_validate(model)
        )

    def _list_customer_devices(self, owner_user_id: str, model: BaseModel) -> Any:
        req = CustomerDeviceListInput.model_validate(model)
        items, total = self.repair_service.list_devices(
            owner_user_id, req.customer_id, offset=req.offset, limit=req.limit
        )
        return {"items": items, "total": total, "offset": req.offset, "limit": req.limit}

    def _register_customer_device(self, owner_user_id: str, model: BaseModel) -> Any:
        return self.repair_service.create_device(
            owner_user_id, CustomerDeviceCreateRequest.model_validate(model)
        )

    def _search_repair_tickets(self, owner_user_id: str, model: BaseModel) -> Any:
        req = RepairTicketSearchInput.model_validate(model)
        items, total = self.repair_service.list_tickets(owner_user_id, **req.model_dump())
        return {"items": items, "total": total, "offset": req.offset, "limit": req.limit}

    def _get_repair_ticket(self, owner_user_id: str, model: BaseModel) -> Any:
        req = RepairTicketLookupInput.model_validate(model)
        return self.repair_service.get_ticket(owner_user_id, req.ticket_id)

    def _create_repair_ticket(self, owner_user_id: str, model: BaseModel) -> Any:
        return self.repair_service.create_ticket(
            owner_user_id, RepairTicketCreateRequest.model_validate(model)
        )

    def _update_repair_status(self, owner_user_id: str, model: BaseModel) -> Any:
        req = RepairTicketStatusInput.model_validate(model)
        status_req = RepairTicketStatusChangeRequest(
            status=req.status,
            reason=req.reason,
        )
        return self.repair_service.change_ticket_status(
            owner_user_id,
            req.ticket_id,
            status_req,
            changed_by_user_id=owner_user_id,
        )

    def _get_repair_status_history(self, owner_user_id: str, model: BaseModel) -> Any:
        req = RepairTicketLookupInput.model_validate(model)
        return self.repair_service.list_ticket_status_history(owner_user_id, req.ticket_id)

    def _add_repair_note(self, owner_user_id: str, model: BaseModel) -> Any:
        req = RepairTicketNoteInput.model_validate(model)
        note_req = RepairTicketNoteCreateRequest(
            note_type=req.note_type,
            body=req.body,
            customer_visible=req.customer_visible,
        )
        return self.repair_service.create_ticket_note(
            owner_user_id,
            req.ticket_id,
            owner_user_id,
            note_req,
        )


__all__ = [
    "REPAIR_TOOL_DEFINITIONS",
    "RepairAssistantTools",
    "RepairToolConfirmationRequired",
    "RepairToolDefinition",
    "RepairToolNotFound",
]

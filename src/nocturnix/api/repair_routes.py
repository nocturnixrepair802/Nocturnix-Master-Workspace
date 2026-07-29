from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Query

from nocturnix.models import UserIdentity
from nocturnix.repair_models import (
    CustomerCreateRequest,
    CustomerDeviceCreateRequest,
    CustomerDeviceListResponse,
    CustomerDeviceResponse,
    CustomerDeviceUpdateRequest,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdateRequest,
    RepairTicketCreateRequest,
    RepairTicketLineItemCreateRequest,
    RepairTicketLineItemResponse,
    RepairTicketLineItemUpdateRequest,
    RepairTicketListResponse,
    RepairTicketNoteCreateRequest,
    RepairTicketNoteResponse,
    RepairTicketNoteUpdateRequest,
    RepairTicketResponse,
    RepairTicketStatusChangeRequest,
    RepairTicketStatusHistoryResponse,
    RepairTicketUpdateRequest,
)


def create_repair_router(
    get_services: Callable[..., Any],
    auth_identity: Callable[..., UserIdentity],
    require_csrf: Callable[..., UserIdentity],
) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["repair-management"])

    @router.post("/customers", response_model=CustomerResponse, status_code=201)
    def create_customer(
        req: CustomerCreateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.create_customer(user.user_id, req)

    @router.get("/customers", response_model=CustomerListResponse)
    def list_customers(
        search: str | None = None,
        status: str | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        items, total = services.repair_domain.list_customers(
            user.user_id,
            search=search,
            status=status,
            offset=offset,
            limit=limit,
        )
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    @router.get("/customers/{customer_id}", response_model=CustomerResponse)
    def get_customer(
        customer_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.get_customer(user.user_id, customer_id)

    @router.put("/customers/{customer_id}", response_model=CustomerResponse)
    def update_customer(
        customer_id: str,
        req: CustomerUpdateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.update_customer(user.user_id, customer_id, req)

    @router.post("/customer-devices", response_model=CustomerDeviceResponse, status_code=201)
    def create_device(
        req: CustomerDeviceCreateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.create_device(user.user_id, req)

    @router.get("/customer-devices/{device_id}", response_model=CustomerDeviceResponse)
    def get_device(
        device_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.get_device(user.user_id, device_id)

    @router.put("/customer-devices/{device_id}", response_model=CustomerDeviceResponse)
    def update_device(
        device_id: str,
        req: CustomerDeviceUpdateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.update_device(user.user_id, device_id, req)

    @router.get("/customers/{customer_id}/devices", response_model=CustomerDeviceListResponse)
    def list_customer_devices(
        customer_id: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        items, total = services.repair_domain.list_devices(
            user.user_id, customer_id, offset=offset, limit=limit
        )
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    @router.post("/repair-tickets", response_model=RepairTicketResponse, status_code=201)
    def create_ticket(
        req: RepairTicketCreateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.create_ticket(user.user_id, req)

    @router.get("/repair-tickets", response_model=RepairTicketListResponse)
    def list_tickets(
        customer_id: str | None = None,
        device_id: str | None = None,
        assigned_user_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        items, total = services.repair_domain.list_tickets(
            user.user_id,
            customer_id=customer_id,
            device_id=device_id,
            assigned_user_id=assigned_user_id,
            status=status,
            priority=priority,
            search=search,
            offset=offset,
            limit=limit,
        )
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    @router.get("/repair-tickets/{ticket_id}", response_model=RepairTicketResponse)
    def get_ticket(
        ticket_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.get_ticket(user.user_id, ticket_id)

    @router.put("/repair-tickets/{ticket_id}", response_model=RepairTicketResponse)
    def update_ticket(
        ticket_id: str,
        req: RepairTicketUpdateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.update_ticket(user.user_id, ticket_id, req)

    @router.post("/repair-tickets/{ticket_id}/status", response_model=RepairTicketResponse)
    def change_ticket_status(
        ticket_id: str,
        req: RepairTicketStatusChangeRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.change_ticket_status(
            user.user_id,
            ticket_id,
            req,
            changed_by_user_id=user.user_id,
        )

    @router.get(
        "/repair-tickets/{ticket_id}/status-history",
        response_model=list[RepairTicketStatusHistoryResponse],
    )
    def list_status_history(
        ticket_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.list_ticket_status_history(user.user_id, ticket_id)

    @router.post(
        "/repair-tickets/{ticket_id}/notes",
        response_model=RepairTicketNoteResponse,
        status_code=201,
    )
    def create_ticket_note(
        ticket_id: str,
        req: RepairTicketNoteCreateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.create_ticket_note(user.user_id, ticket_id, user.user_id, req)

    @router.get(
        "/repair-tickets/{ticket_id}/notes",
        response_model=list[RepairTicketNoteResponse],
    )
    def list_ticket_notes(
        ticket_id: str,
        customer_visible_only: bool = False,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        items, _total = services.repair_domain.list_ticket_notes(
            user.user_id,
            ticket_id,
            customer_visible_only=customer_visible_only,
            offset=offset,
            limit=limit,
        )
        return items

    @router.put("/repair-ticket-notes/{note_id}", response_model=RepairTicketNoteResponse)
    def update_ticket_note(
        note_id: str,
        req: RepairTicketNoteUpdateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.update_ticket_note(user.user_id, note_id, req)

    @router.post(
        "/repair-tickets/{ticket_id}/line-items",
        response_model=RepairTicketLineItemResponse,
        status_code=201,
    )
    def create_ticket_line_item(
        ticket_id: str,
        req: RepairTicketLineItemCreateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.create_ticket_line_item(
            user.user_id,
            ticket_id,
            req,
        )

    @router.get(
        "/repair-tickets/{ticket_id}/line-items",
        response_model=list[RepairTicketLineItemResponse],
    )
    def list_ticket_line_items(
        ticket_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.list_ticket_line_items(
            user.user_id,
            ticket_id,
        )

    @router.get(
        "/repair-ticket-line-items/{line_item_id}",
        response_model=RepairTicketLineItemResponse,
    )
    def get_ticket_line_item(
        line_item_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.get_ticket_line_item(
            user.user_id,
            line_item_id,
        )

    @router.put(
        "/repair-ticket-line-items/{line_item_id}",
        response_model=RepairTicketLineItemResponse,
    )
    def update_ticket_line_item(
        line_item_id: str,
        req: RepairTicketLineItemUpdateRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        return services.repair_domain.update_ticket_line_item(
            user.user_id,
            line_item_id,
            req,
        )

    @router.delete(
        "/repair-ticket-line-items/{line_item_id}",
        status_code=204,
    )
    def delete_ticket_line_item(
        line_item_id: str,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> None:
        services.repair_domain.delete_ticket_line_item(
            user.user_id,
            line_item_id,
        )

    return router

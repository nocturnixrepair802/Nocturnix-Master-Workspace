from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends

from nocturnix.models import UserIdentity
from nocturnix.repair_models import RepairDashboardResponse


def create_repair_dashboard_router(
    get_services: Callable[..., Any],
    auth_identity: Callable[..., UserIdentity],
) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["repair-dashboard"])

    @router.get("/repair-dashboard", response_model=RepairDashboardResponse)
    def repair_dashboard(
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.repair_domain.repair_dashboard(user.user_id)

    return router

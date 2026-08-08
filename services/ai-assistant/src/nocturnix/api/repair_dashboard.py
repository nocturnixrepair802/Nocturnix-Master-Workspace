from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from nocturnix.models import UserIdentity
from nocturnix.repair_models import RepairDashboardResponse

_DASHBOARD_FILE = Path(__file__).resolve().parent.parent / "static" / "repairs-dashboard.html"


def create_repair_dashboard_router(
    get_services: Callable[..., Any],
    auth_identity: Callable[..., UserIdentity],
) -> APIRouter:
    router = APIRouter(tags=["repair-dashboard"])

    @router.get(
        "/dashboard/repairs",
        response_class=FileResponse,
        include_in_schema=False,
    )
    def repair_dashboard_page(
        user: UserIdentity = Depends(auth_identity),
    ) -> FileResponse:
        return FileResponse(_DASHBOARD_FILE)

    @router.get(
        "/api/v1/dashboard/repairs",
        response_model=RepairDashboardResponse,
    )
    def repair_dashboard_data(
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ) -> RepairDashboardResponse:
        return services.repair_domain.repair_dashboard(user.user_id)

    return router

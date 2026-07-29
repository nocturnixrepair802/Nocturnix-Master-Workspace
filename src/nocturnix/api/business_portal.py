from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from nocturnix.models import UserIdentity

_PORTAL_FILE = (
    Path(__file__).resolve().parent.parent
    / "static"
    / "business-portal.html"
)


def create_business_portal_router(
    auth_identity: Callable[..., UserIdentity],
) -> APIRouter:
    router = APIRouter(tags=["business-portal"])

    @router.get(
        "/dashboard",
        response_class=FileResponse,
        include_in_schema=False,
    )
    def business_portal_page(
        user: UserIdentity = Depends(auth_identity),
    ) -> FileResponse:
        return FileResponse(_PORTAL_FILE)

    return router

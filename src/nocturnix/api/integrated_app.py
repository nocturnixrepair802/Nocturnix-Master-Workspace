from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from nocturnix.api import app as base_app
from nocturnix.api.repair_routes import create_repair_router
from nocturnix.config import Settings
from nocturnix.models import UserIdentity
from nocturnix.repair_services import (
    InvalidRepairStatusTransition,
    RepairConflict,
    RepairResourceNotFound,
    RepairService as RepairDomainService,
)
from nocturnix.security.auth import AuthService, stable_hash


def _install_request_service_extension() -> None:
    if getattr(base_app.RequestServices, "_repair_domain_installed", False):
        return

    original_init = base_app.RequestServices.__init__

    def integrated_init(self, container):
        original_init(self, container)
        self.repair_domain = RepairDomainService(self.session)

    base_app.RequestServices.__init__ = integrated_init
    base_app.RequestServices._repair_domain_installed = True


def create_app(settings: Settings | None = None):
    _install_request_service_extension()
    app = base_app.create_app(settings)

    def auth_identity(
        request: Request,
        services=Depends(base_app.get_services),
        x_nocturnix_dev_user: str | None = Header(default=None),
        nocturnix_session: str | None = Cookie(default=None),
    ) -> UserIdentity:
        resolved_settings = services.container.settings
        if resolved_settings.auth_mode == "disabled":
            raise HTTPException(status_code=401, detail="authentication disabled")
        if resolved_settings.auth_mode == "development_header":
            if (
                not resolved_settings.allow_development_header_auth
                or not resolved_settings.dev_identity_enabled
                or not x_nocturnix_dev_user
            ):
                raise HTTPException(
                    status_code=401,
                    detail="development identity header required",
                )
            return UserIdentity(
                user_id=x_nocturnix_dev_user,
                display_name="Development Header User",
                auth_mode="development_header",
            )

        raw = request.cookies.get(resolved_settings.session_cookie_name) or nocturnix_session
        if not raw:
            raise HTTPException(status_code=401, detail="authenticated session required")
        resolved_user = AuthService(services.session, resolved_settings).user_for_token(raw)
        if not resolved_user:
            raise HTTPException(status_code=401, detail="authenticated session required")
        user, session = resolved_user
        request.state.nocturnix_session_id = session.id
        request.state.nocturnix_csrf_hash = session.csrf_token_hash
        return UserIdentity(
            user_id=user.id,
            display_name=user.display_name,
            auth_mode="session",
        )

    def require_csrf(
        request: Request,
        user: UserIdentity = Depends(auth_identity),
        x_csrf_token: str | None = Header(default=None),
    ) -> UserIdentity:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = getattr(request.state, "nocturnix_csrf_hash", None)
            if user.auth_mode == "session" and (
                not x_csrf_token or stable_hash(x_csrf_token) != expected
            ):
                raise HTTPException(status_code=403, detail="invalid CSRF token")
        return user

    def error_response(request: Request, status_code: int, code: str, message: str):
        return JSONResponse(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": request.headers.get("x-request-id", "unknown"),
                    "details": None,
                }
            },
            status_code=status_code,
        )

    @app.exception_handler(RepairResourceNotFound)
    async def repair_not_found(request: Request, exc: RepairResourceNotFound):
        return error_response(request, 404, "repair_not_found", str(exc))

    @app.exception_handler(InvalidRepairStatusTransition)
    async def invalid_status_transition(
        request: Request, exc: InvalidRepairStatusTransition
    ):
        return error_response(request, 409, "invalid_repair_status_transition", str(exc))

    @app.exception_handler(RepairConflict)
    async def repair_conflict(request: Request, exc: RepairConflict):
        return error_response(request, 409, "repair_conflict", str(exc))

    app.include_router(
        create_repair_router(
            base_app.get_services,
            auth_identity,
            require_csrf,
        )
    )
    return app


__all__ = ["create_app"]

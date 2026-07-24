from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from time import monotonic
from typing import Any, cast
from uuid import uuid4
from weakref import finalize

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from nocturnix.config import Settings
from nocturnix.db import (
    create_database_engine,
    create_session_factory,
    current_revision,
    database_ready,
    run_migrations,
    safe_database_provider,
    session_scope,
)
from nocturnix.models import (
    APP_NAME,
    APP_VERSION,
    DEV_USER_ID,
    ApprovalCreateRequest,
    CalendarProposal,
    ChatRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    PreferencesUpdateRequest,
    RepairIntakeRequest,
    RetentionCleanupRequest,
    RiskLevel,
    UserIdentity,
)
from nocturnix.persistence_models import (
    CodexTaskRecordRow,
    ConversationRow,
    ProviderAccountRow,
    RecurrenceRuleRow,
    ReminderRow,
    RepairContextRow,
    SessionRow,
    UserRow,
)
from nocturnix.repositories.sql import (
    SqlApprovalRepository,
    SqlAuditRepository,
    SqlConversationRepository,
    SqlMessageRepository,
    SqlPreferenceRepository,
    SqlRepairIntakeRepository,
)
from nocturnix.security.auth import (
    AuthorizationService,
    AuthService,
    OAuthService,
    PasswordResetService,
    stable_hash,
)
from nocturnix.services.business import (
    BusinessService,
    InAppMockNotificationProvider,
    make_id,
)
from nocturnix.services.core import (
    ApprovalConflict,
    ApprovalService,
    AuditService,
    ConversationService,
    KnowledgeService,
    MockAssistantProvider,
    NotFound,
    PermissionDenied,
    PreferenceService,
    RepairService,
    RetentionService,
)


class AppContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine = create_database_engine(settings.database_url, settings.database_echo)
        self._engine_finalizer = finalize(self, self.engine.dispose)
        if settings.database_migration_mode == "auto-test-only":
            run_migrations(settings.database_url)
        self.session_factory = create_session_factory(self.engine)
        self.knowledge = KnowledgeService(settings.safe_knowledge_path)
        self.assistant = MockAssistantProvider()
        self.rate_buckets: dict[str, list[float]] = defaultdict(list)


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


class RequestServices:
    def __init__(self, container: AppContainer):
        self.container = container
        self.scope = session_scope(container.session_factory)
        self.session = self.scope.__enter__()
        self.audit = AuditService(SqlAuditRepository(self.session))
        self.approvals = ApprovalService(SqlApprovalRepository(self.session), self.audit)
        self.conversations = ConversationService(
            SqlConversationRepository(self.session),
            SqlMessageRepository(self.session),
            container.settings.conversation_retention_days,
        )
        self.repair_repo = SqlRepairIntakeRepository(self.session)
        self.preferences = PreferenceService(SqlPreferenceRepository(self.session))
        self.retention = RetentionService(self.audit, container.settings)
        self.repair = RepairService()

    def close(self) -> None:
        self.scope.__exit__(None, None, None)


def get_services(request: Request):
    services = RequestServices(request.app.state.container)
    try:
        yield services
    except Exception as exc:
        services.scope.__exit__(type(exc), exc, exc.__traceback__)
        raise
    else:
        services.close()


def current_user(x_nocturnix_dev_user: str | None = Header(default=None)) -> UserIdentity:
    if x_nocturnix_dev_user is None:
        raise HTTPException(status_code=401, detail="development identity header required")
    return UserIdentity(user_id=x_nocturnix_dev_user or DEV_USER_ID)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ready = True
        yield
        app.state.container.engine.dispose()
        app.state.ready = False

    app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
    app.state.container = AppContainer(resolved)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "X-Nocturnix-Dev-User", "X-Request-ID", "X-CSRF-Token"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", f"req_{uuid4().hex[:12]}")
        client_key = request.client.host if request.client else "test-client"
        bucket = app.state.container.rate_buckets[client_key]
        now = monotonic()
        bucket[:] = [entry for entry in bucket if now - entry < 60]
        if len(bucket) >= resolved.rate_limit_per_minute:
            return JSONResponse(
                {
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests",
                        "request_id": request_id,
                    }
                },
                status_code=429,
                headers={"X-Request-ID": request_id},
            )
        bucket.append(now)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    def error_response(
        request: Request, status_code: int, code: str, message: str, details: object | None = None
    ) -> JSONResponse:
        return JSONResponse(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": request.headers.get("x-request-id", "unknown"),
                    "details": jsonable_encoder(details),
                }
            },
            status_code=status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return error_response(
            request, 422, "validation_error", "Request validation failed", exc.errors()
        )

    @app.exception_handler(NotFound)
    async def not_found(request: Request, exc: NotFound):
        return error_response(request, 404, "not_found", str(exc))

    @app.exception_handler(PermissionDenied)
    async def permission_denied(request: Request, exc: PermissionDenied):
        return error_response(request, 403, "permission_denied", str(exc))

    @app.exception_handler(ApprovalConflict)
    async def approval_conflict(request: Request, exc: ApprovalConflict):
        return error_response(request, 409, "approval_conflict", str(exc))

    def auth_identity(
        request: Request,
        services: RequestServices = Depends(get_services),
        x_nocturnix_dev_user: str | None = Header(default=None),
        nocturnix_session: str | None = Cookie(default=None),
    ) -> UserIdentity:
        settings = services.container.settings
        if settings.auth_mode == "disabled":
            raise HTTPException(status_code=401, detail="authentication disabled")
        if settings.auth_mode == "development_header":
            if (
                not settings.allow_development_header_auth
                or not settings.dev_identity_enabled
                or not x_nocturnix_dev_user
            ):
                raise HTTPException(status_code=401, detail="development identity header required")
            return UserIdentity(
                user_id=x_nocturnix_dev_user,
                display_name="Development Header User",
                auth_mode="development_header",
            )
        raw = request.cookies.get(settings.session_cookie_name) or nocturnix_session
        if not raw:
            raise HTTPException(status_code=401, detail="authenticated session required")
        resolved_user = AuthService(services.session, settings).user_for_token(raw)
        if not resolved_user:
            raise HTTPException(status_code=401, detail="authenticated session required")
        user, session = resolved_user
        request.state.nocturnix_session_id = session.id
        request.state.nocturnix_csrf_hash = session.csrf_token_hash
        return UserIdentity(user_id=user.id, display_name=user.display_name, auth_mode="session")

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

    def require_perm(permission: str):
        def checker(
            user: UserIdentity = Depends(auth_identity),
            services: RequestServices = Depends(get_services),
        ) -> UserIdentity:
            AuthorizationService(services.session).require(user, permission)
            return user

        return checker

    @app.get("/api/v1/health")
    def health(container: AppContainer = Depends(get_container)):
        return {
            "status": "ok",
            "application": APP_NAME,
            "version": APP_VERSION,
            "environment": container.settings.environment,
            "mock_providers_enabled": container.settings.mock_providers_enabled,
        }

    @app.get("/api/v1/config/public")
    def public_config(container: AppContainer = Depends(get_container)):
        return {
            "application": APP_NAME,
            "version": APP_VERSION,
            "contact_message": container.settings.public_contact_message,
            "auth_mode": container.settings.auth_mode,
        }

    @app.get("/api/v1/status")
    def status(
        container: AppContainer = Depends(get_container),
        user: UserIdentity = Depends(auth_identity),
    ):
        return {
            "mock_ai_provider_enabled": True,
            "mock_email_provider_enabled": True,
            "mock_calendar_provider_enabled": True,
            "external_providers_disabled": not container.settings.external_providers_enabled,
            "knowledge_base_available": container.settings.safe_knowledge_path.exists(),
            "approval_service_available": True,
            "audit_service_available": True,
            "persistence_type": "durable SQL development storage",
            "persistence_provider": safe_database_provider(container.settings.database_url),
            "database_ready": database_ready(container.settings.database_url),
            "migration_revision": current_revision(container.settings.database_url),
            "authentication_mode": container.settings.auth_mode,
            "session_storage_available": True,
            "rbac_available": True,
            "secret_storage_enabled": container.settings.secret_storage_enabled,
            "mock_oauth_available": container.settings.mock_oauth_enabled,
            "provider_integrations_disabled": True,
            "retention_configured": True,
            "ready": True,
            "user_id": user.user_id,
        }

    @app.post("/api/v1/chat")
    def chat(
        req: ChatRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(require_perm("assistant.chat")),
    ):
        sources, _placeholder = services.container.knowledge.search(req.message, limit=3)
        response = services.container.assistant.respond(req.message, req.conversation_id, sources)
        services.audit.record(user, "chat", "created", metadata={"escalation": response.escalation})
        services.conversations.persist_exchange(user, req, response)
        return response

    @app.post("/api/v1/knowledge/search", response_model=KnowledgeSearchResponse)
    def knowledge_search(
        req: KnowledgeSearchRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(require_perm("assistant.chat")),
    ):
        services.audit.record(user, "knowledge", "searched")
        results, placeholder = services.container.knowledge.search(req.query, req.limit)
        return KnowledgeSearchResponse(results=results, placeholder=placeholder)

    @app.post("/api/v1/repair-intakes")
    def repair_intake(
        req: RepairIntakeRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(require_perm("repair_intake.create")),
    ):
        resp = services.repair.create(user, req, services.audit)
        from datetime import UTC, datetime, timedelta

        from nocturnix.models import RepairIntakeRecord

        now = datetime.now(UTC)
        services.repair_repo.add(
            RepairIntakeRecord(
                id=resp.id,
                owner_user_id=user.user_id,
                device_type=req.device_type,
                manufacturer=req.manufacturer,
                model=req.model,
                issue_description=req.issue_description,
                power_state=req.power_state,
                physical_damage_state=req.visible_damage,
                liquid_exposure_state=req.liquid_exposure,
                data_recovery_importance=req.data_recovery_importance,
                preferred_service_method=req.preferred_service_method,
                desired_next_step=req.desired_next_step,
                notes=req.notes,
                escalation_state="escalated" if resp.safety_escalation else "none",
                escalation_reason=", ".join(resp.safety_indicators) or None,
                status="draft",
                created_at=now,
                updated_at=now,
                retention_expires_at=now
                + timedelta(days=services.container.settings.repair_intake_retention_days),
            )
        )
        return resp

    @app.post("/api/v1/approvals")
    def create_approval(
        req: ApprovalCreateRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.approvals.create(user, req)

    @app.get("/api/v1/approvals")
    def list_approvals(
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return {"items": services.approvals.list(user)}

    @app.get("/api/v1/approvals/{approval_id}")
    def get_approval(
        approval_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.approvals.get(user, approval_id)

    @app.post("/api/v1/approvals/{approval_id}/approve")
    def approve(
        approval_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.approvals.approve(user, approval_id)

    @app.post("/api/v1/approvals/{approval_id}/reject")
    def reject(
        approval_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.approvals.reject(user, approval_id)

    @app.get("/api/v1/audit")
    def audit(
        offset: int = 0,
        limit: int = 20,
        category: str | None = None,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return {
            "items": services.audit.list(user, category, offset, limit),
            "offset": offset,
            "limit": min(limit, 100),
        }

    email_messages = [
        {
            "id": "msg_1",
            "from": "alex@example.test",
            "to": "owner@example.test",
            "subject": "Mock repair update",
            "body": "Fictional .test message about preparing a device for service.",
            "classification": "normal",
            "mock": True,
        },
        {
            "id": "msg_2",
            "from": "billing@example.test",
            "to": "owner@example.test",
            "subject": "Mock restricted request",
            "body": "Fictional restricted payment-related request. No real data.",
            "classification": "restricted",
            "mock": True,
        },
    ]

    @app.get("/api/v1/mock/email/messages")
    def list_email(user: UserIdentity = Depends(auth_identity)):
        return {"mock": True, "items": email_messages}

    @app.get("/api/v1/mock/email/messages/{message_id}")
    def get_email(message_id: str, user: UserIdentity = Depends(auth_identity)):
        return next(
            (m for m in email_messages if m["id"] == message_id),
            (_ for _ in ()).throw(NotFound("email not found")),
        )

    @app.post("/api/v1/mock/email/messages/{message_id}/summarize")
    def summarize_email(message_id: str, user: UserIdentity = Depends(auth_identity)):
        return {
            "mock": True,
            "message_id": message_id,
            "summary": "Fictional email summary. Gmail is not connected.",
        }

    @app.post("/api/v1/mock/email/messages/{message_id}/draft-proposal")
    def email_draft(
        message_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        approval = services.approvals.create(
            user,
            ApprovalCreateRequest(
                action_type="mock_email_draft",
                provider="mock_email",
                resource=message_id,
                title="Draft mock email reply",
                proposed_content={
                    "message_id": message_id,
                    "draft": "Fictional draft only; send is not implemented.",
                },
                risk_level=RiskLevel.medium,
            ),
        )
        return {"mock": True, "approval": approval}

    calendar_events = [
        {
            "id": "evt_1",
            "title": "Mock repair consultation",
            "start": "2026-07-23T10:00:00+00:00",
            "end": "2026-07-23T10:30:00+00:00",
            "time_zone": "UTC",
            "attendees": ["owner@example.test"],
            "location": "Mock bench",
            "description": "Fictional calendar event.",
            "mock": True,
        }
    ]

    @app.get("/api/v1/mock/calendar/events")
    def list_calendar(user: UserIdentity = Depends(auth_identity)):
        return {"mock": True, "items": calendar_events}

    @app.post("/api/v1/mock/calendar/event-proposals")
    def calendar_proposal(
        req: CalendarProposal,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        conflict = any(
            str(event["start"]).startswith(req.start.strftime("%Y-%m-%dT%H"))
            for event in calendar_events
        )
        approval = services.approvals.create(
            user,
            ApprovalCreateRequest(
                action_type="mock_calendar_event",
                provider="mock_calendar",
                title=req.title,
                proposed_content=req.model_dump(mode="json"),
                risk_level=RiskLevel.medium,
            ),
        )
        return {"mock": True, "conflict_detected": conflict, "approval": approval}

    @app.get("/api/v1/preferences")
    def get_preferences(
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.preferences.get(user)

    @app.put("/api/v1/preferences")
    def put_preferences(
        req: PreferencesUpdateRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.preferences.update(user, req)

    @app.post("/api/v1/retention/cleanup")
    def retention_cleanup(
        req: RetentionCleanupRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        return services.retention.cleanup(user, dry_run=req.dry_run)

    @app.post("/api/v1/auth/register")
    def auth_register(
        req: dict[str, str],
        response: Response,
        request: Request,
        services: RequestServices = Depends(get_services),
    ):
        if not services.container.settings.allow_development_registration:
            raise HTTPException(status_code=403, detail="development registration disabled")
        user = AuthService(services.session, services.container.settings).create_user(
            req.get("email", ""),
            req.get("password", ""),
            req.get("display_name", "Development User"),
            req.get("role", "owner"),
        )
        return {
            "id": user.id,
            "login_identifier": user.login_identifier,
            "display_name": user.display_name,
            "account_status": user.account_status,
            "roles": [req.get("role", "owner")],
        }

    @app.post("/api/v1/auth/login")
    def auth_login(
        req: dict[str, str],
        response: Response,
        request: Request,
        services: RequestServices = Depends(get_services),
    ):
        try:
            user, token, csrf = AuthService(services.session, services.container.settings).login(
                req.get("email", ""), req.get("password", ""), request.headers.get("user-agent")
            )
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        settings = services.container.settings
        response.set_cookie(
            settings.session_cookie_name,
            token,
            httponly=True,
            secure=settings.session_cookie_secure,
            samesite="lax",
            max_age=settings.session_absolute_hours * 3600,
        )
        return {
            "user": {
                "id": user.id,
                "login_identifier": user.login_identifier,
                "display_name": user.display_name,
            },
            "csrf_token": csrf,
        }

    @app.get("/api/v1/auth/me")
    def auth_me(
        user: UserIdentity = Depends(auth_identity),
        services: RequestServices = Depends(get_services),
    ):
        permissions = sorted(
            AuthorizationService(services.session).permissions_for_user(user.user_id)
        )
        return {
            "id": user.user_id,
            "display_name": user.display_name,
            "auth_mode": user.auth_mode,
            "permissions": permissions,
        }

    @app.post("/api/v1/auth/logout")
    def auth_logout(
        response: Response,
        request: Request,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        sid = getattr(request.state, "nocturnix_session_id", None)
        if sid:
            AuthService(services.session, services.container.settings).revoke(
                sid, user.user_id, "logout"
            )
        response.delete_cookie(services.container.settings.session_cookie_name)
        return {"revoked": True}

    @app.get("/api/v1/auth/sessions")
    def auth_sessions(
        user: UserIdentity = Depends(require_perm("security_sessions.read")),
        services: RequestServices = Depends(get_services),
    ):
        rows = services.session.scalars(
            select(SessionRow).where(SessionRow.user_id == user.user_id)
        ).all()
        return {
            "items": [
                {
                    "id": r.id,
                    "created_at": r.created_at,
                    "last_seen_at": r.last_seen_at,
                    "expires_at": r.expires_at,
                    "absolute_expires_at": r.absolute_expires_at,
                    "revoked_at": r.revoked_at,
                    "revocation_reason": r.revocation_reason,
                }
                for r in rows
            ]
        }

    @app.post("/api/v1/auth/sessions/revoke-all")
    def auth_revoke_all(
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        count = AuthService(services.session, services.container.settings).revoke_all(user.user_id)
        return {"revoked_count": count}

    @app.post("/api/v1/auth/sessions/{session_id}/revoke")
    def auth_revoke_session(
        session_id: str,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        ok = AuthService(services.session, services.container.settings).revoke(
            session_id, user.user_id, "user_requested"
        )
        if not ok:
            raise HTTPException(status_code=404, detail="session not found")
        return {"revoked": True}

    @app.post("/api/v1/auth/password/change")
    def auth_password_change(
        req: dict[str, str],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        row = services.session.get(UserRow, user.user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="user not found")
        try:
            AuthService(services.session, services.container.settings).change_password(
                row, req.get("current_password", ""), req.get("new_password", "")
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"changed": True}

    @app.post("/api/v1/auth/password/reset/request")
    def auth_reset_request(req: dict[str, str], services: RequestServices = Depends(get_services)):
        return PasswordResetService(services.session, services.container.settings).request(
            req.get("email", "")
        )

    @app.post("/api/v1/auth/password/reset/complete")
    def auth_reset_complete(req: dict[str, str], services: RequestServices = Depends(get_services)):
        try:
            PasswordResetService(services.session, services.container.settings).complete(
                req.get("reset_token", ""), req.get("new_password", "")
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"reset": True}

    def _oauth_scopes(req: dict[str, object]) -> list[str]:
        value = req.get("scopes")
        if not isinstance(value, list):
            return []
        return [str(scope) for scope in value]

    @app.post("/api/v1/oauth/{provider}/authorize")
    def oauth_authorize(
        provider: str,
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        try:
            return OAuthService(services.session, services.container.settings).start(
                user.user_id,
                provider,
                str(req.get("redirect_uri", "")),
                _oauth_scopes(req),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/oauth/{provider}/callback")
    def oauth_callback(
        provider: str,
        state: str,
        pkce_verifier: str,
        error: str | None = None,
        user: UserIdentity = Depends(auth_identity),
        services: RequestServices = Depends(get_services),
    ):
        try:
            acct = OAuthService(services.session, services.container.settings).callback(
                user.user_id, provider, state, pkce_verifier, error
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"mock": True, "provider_account_id": acct.id, "status": acct.status}

    @app.get("/api/v1/provider-accounts")
    def provider_accounts(
        user: UserIdentity = Depends(require_perm("provider_accounts.read")),
        services: RequestServices = Depends(get_services),
    ):
        rows = services.session.scalars(
            select(ProviderAccountRow).where(ProviderAccountRow.owner_user_id == user.user_id)
        ).all()
        return {
            "items": [
                {
                    "id": r.id,
                    "provider_name": r.provider_name,
                    "display_label": r.display_label,
                    "requested_scopes": r.requested_scopes,
                    "granted_scopes": r.granted_scopes,
                    "linked_at": r.linked_at,
                    "revoked_at": r.revoked_at,
                    "status": r.status,
                    "mock": True,
                }
                for r in rows
            ]
        }

    @app.get("/api/v1/provider-accounts/{provider_account_id}")
    def provider_account(
        provider_account_id: str,
        user: UserIdentity = Depends(require_perm("provider_accounts.read")),
        services: RequestServices = Depends(get_services),
    ):
        r = services.session.get(ProviderAccountRow, provider_account_id)
        if not r or r.owner_user_id != user.user_id:
            raise HTTPException(status_code=404, detail="provider account not found")
        return {
            "id": r.id,
            "provider_name": r.provider_name,
            "display_label": r.display_label,
            "status": r.status,
            "mock": True,
        }

    @app.post("/api/v1/provider-accounts/{provider_account_id}/revoke")
    def provider_revoke(
        provider_account_id: str,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        if not OAuthService(services.session, services.container.settings).revoke(
            user.user_id, provider_account_id
        ):
            raise HTTPException(status_code=404, detail="provider account not found")
        return {"revoked": True}

    @app.get("/api/v1/widget/config")
    def widget_config(user: UserIdentity = Depends(auth_identity)):
        return {
            "mock": True,
            "version": APP_VERSION,
            "development_warning": "Development-only mock widget. No live providers are connected.",
            "context_modes": ["public", "customer", "technician", "owner"],
            "features": ["chat", "tasks", "reminders", "focus_now", "repair_copilot"],
            "user_id": user.user_id,
        }

    @app.get("/api/v1/conversations")
    def list_conversations(
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        rows = services.session.scalars(
            select(ConversationRow)
            .where(ConversationRow.owner_user_id == user.user_id)
            .order_by(ConversationRow.updated_at.desc())
        ).all()
        return {
            "items": [
                {
                    "id": r.id,
                    "mode": r.mode,
                    "status": r.status,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                    "context_mode": r.mode,
                }
                for r in rows
            ]
        }

    @app.post("/api/v1/conversations")
    def create_conversation(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        mode = str(req.get("context_mode") or "owner")
        if mode not in {"public", "customer", "technician", "owner"}:
            raise HTTPException(status_code=400, detail="invalid context mode")
        if mode == "owner":
            AuthorizationService(services.session).require(user, "assistant.chat")
        now = datetime.now(UTC)
        row = ConversationRow(
            id=f"conv_{uuid4().hex[:12]}",
            owner_user_id=user.user_id,
            mode=mode,
            status="active",
            created_at=now,
            updated_at=now,
            retention_expires_at=now
            + timedelta(days=services.container.settings.conversation_retention_days),
        )
        services.session.add(row)
        return {"id": row.id, "context_mode": mode, "mock": True}

    @app.post("/api/v1/widget/messages")
    def widget_message(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        text = str(req.get("message") or "").strip()
        mode = str(req.get("context_mode") or "owner")
        if "owner mode" in text.lower() and mode != "owner":
            mode = str(req.get("context_mode") or "public")
        biz = BusinessService(services.session)
        if "focus" in text.lower():
            payload = biz.focus_now(user.user_id)
            response = "Here are up to three Focus Now items."
        elif "waiting" in text.lower():
            payload = biz.waiting_on(user.user_id)
            response = "Here is what is waiting on someone or something else."
        elif "briefing" in text.lower():
            payload = biz.briefing(user.user_id)
            response = "Here is a mock daily business briefing."
        elif "close out" in text.lower() or "end of day" in text.lower():
            payload = biz.end_of_day(user.user_id)
            response = "Here are gentle end-of-day recovery choices."
        elif text.lower().startswith("remind me"):
            when = datetime.now(UTC) + timedelta(days=1)
            row = ReminderRow(
                id=make_id("rem"),
                owner_user_id=user.user_id,
                reminder_type="scheduled",
                scheduled_at=when,
                next_delivery_at=when,
                status="scheduled",
                priority="normal",
                delivery_channel="in_app_mock",
                title=text[:200],
                created_at=datetime.now(UTC),
            )
            services.session.add(row)
            payload = {"reminder_id": row.id}
            response = "I captured that as a mock in-app reminder for tomorrow."
        else:
            payload = {
                "supported_commands": [
                    "remind me tomorrow",
                    "what should I focus on",
                    "what am I waiting on",
                    "prepare my morning briefing",
                    "close out my day",
                    "track this Codex task",
                    "draft a customer update for this repair",
                ]
            }
            response = (
                "Mock assistant response: I can help capture tasks, reminders, "
                "focus items, and repair-copilot drafts."
            )
        return {
            "mock": True,
            "context_mode": mode,
            "response": response,
            "typing_simulation": True,
            "payload": payload,
            "proposed_actions": [],
        }

    @app.get("/api/v1/tasks")
    def list_tasks(
        status: str | None = None,
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        return {"items": BusinessService(services.session).list_tasks(user.user_id, status)}

    @app.post("/api/v1/tasks")
    def create_task(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        return BusinessService(services.session).create_task(user.user_id, req)

    @app.post("/api/v1/tasks/{task_id}/complete")
    def complete_task(
        task_id: str,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        try:
            return BusinessService(services.session).complete(user.user_id, task_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc

    @app.post("/api/v1/tasks/{task_id}/snooze")
    def snooze_task(
        task_id: str,
        req: dict[str, datetime],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        try:
            return BusinessService(services.session).snooze(user.user_id, task_id, req["until"])
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc

    @app.post("/api/v1/tasks/{task_id}/reschedule")
    def reschedule_task(
        task_id: str,
        req: dict[str, datetime],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        try:
            return BusinessService(services.session).reschedule(
                user.user_id, task_id, req["due_at"]
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc

    @app.get("/api/v1/waiting-on")
    def waiting_on(
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        return BusinessService(services.session).waiting_on(user.user_id)

    @app.get("/api/v1/focus-now")
    def focus_now(
        available_minutes: int = 30,
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        return BusinessService(services.session).focus_now(user.user_id, available_minutes)

    @app.get("/api/v1/daily-briefing")
    def daily_briefing(
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        return BusinessService(services.session).briefing(user.user_id)

    @app.get("/api/v1/end-of-day-review")
    def eod(
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        return BusinessService(services.session).end_of_day(user.user_id)

    @app.get("/api/v1/reminders")
    def list_reminders(
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        rows = services.session.scalars(
            select(ReminderRow)
            .where(ReminderRow.owner_user_id == user.user_id)
            .order_by(ReminderRow.scheduled_at)
        ).all()
        return {"items": [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows]}

    @app.post("/api/v1/reminders")
    def create_reminder(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        scheduled = req.get("scheduled_at") or datetime.now(UTC) + timedelta(hours=1)
        now = datetime.now(UTC)
        row = ReminderRow(
            id=make_id("rem"),
            owner_user_id=user.user_id,
            related_task_id=req.get("related_task_id"),
            related_repair_id=req.get("related_repair_id"),
            reminder_type=str(req.get("reminder_type") or "scheduled"),
            scheduled_at=scheduled,
            next_delivery_at=scheduled,
            trigger_condition=req.get("trigger_condition"),
            status="scheduled",
            priority=str(req.get("priority") or "normal"),
            delivery_channel="in_app_mock",
            quiet_hour_handling=str(req.get("quiet_hour_handling") or "bundle"),
            title=str(req.get("title") or "Reminder")[:200],
            created_at=now,
        )
        services.session.add(row)
        return {"id": row.id, "mock": True}

    @app.post("/api/v1/reminders/{reminder_id}/deliver-mock")
    def deliver_mock(
        reminder_id: str,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        row = services.session.get(ReminderRow, reminder_id)
        if not row or row.owner_user_id != user.user_id:
            raise HTTPException(status_code=404, detail="reminder not found")
        return {
            "event_id": InAppMockNotificationProvider().deliver(services.session, row).id,
            "mock": True,
        }

    @app.get("/api/v1/reminder-preferences")
    def reminder_preferences(user: UserIdentity = Depends(require_perm("preferences.read"))):
        return {
            "workday_start": "09:00",
            "workday_end": "17:00",
            "quiet_hours": {"start": "20:00", "end": "08:00"},
            "maximum_non_urgent_reminders_per_hour": 3,
            "digest_mode": True,
            "urgent_only_mode": False,
            "default_snooze_minutes": 30,
            "reminder_categories_enabled": ["scheduled", "follow_up", "review", "safety"],
            "morning_briefing_time": "08:45",
            "end_of_day_review_time": "16:45",
            "critical_safety_requires_confirmation_to_disable": True,
        }

    @app.post("/api/v1/recurrence-rules")
    def create_recurrence(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        freq = str(req.get("frequency") or "daily")
        if freq not in {"daily", "selected_weekdays", "weekly", "monthly", "interval"}:
            raise HTTPException(status_code=400, detail="invalid recurrence frequency")
        row = RecurrenceRuleRow(
            id=make_id("recur"),
            owner_user_id=user.user_id,
            frequency=freq,
            interval=int(cast(Any, req.get("interval") or 1)),
            weekdays=req.get("weekdays") or [],
            day_of_month=req.get("day_of_month"),
            start_at=req.get("start_at") or datetime.now(UTC),
            end_at=req.get("end_at"),
            template=req.get("template") or {},
            created_at=datetime.now(UTC),
        )
        services.session.add(row)
        return {"id": row.id, "mock": True}

    @app.get("/api/v1/repair-contexts")
    def repair_contexts(
        context_mode: str = "owner",
        user: UserIdentity = Depends(require_perm("repair_intake.read")),
        services: RequestServices = Depends(get_services),
    ):
        if context_mode == "public":
            return {"items": []}
        rows = services.session.scalars(
            select(RepairContextRow).where(RepairContextRow.owner_user_id == user.user_id)
        ).all()
        return {"items": [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows]}

    @app.post("/api/v1/repair-contexts")
    def create_repair_context(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        AuthorizationService(services.session).require(user, "repair_intake.create")
        now = datetime.now(UTC)
        row = RepairContextRow(
            id=make_id("rctx"),
            owner_user_id=user.user_id,
            context_mode=str(req.get("context_mode") or "owner"),
            device_type=str(req.get("device_type") or "device"),
            manufacturer=req.get("manufacturer"),
            model=req.get("model"),
            reported_issue=str(req.get("reported_issue") or "Mock issue"),
            current_status=str(req.get("current_status") or "intake"),
            assigned_technician=req.get("assigned_technician"),
            customer_approval_state=str(req.get("customer_approval_state") or "not_requested"),
            parts_state=str(req.get("parts_state") or "not_checked"),
            target_at=req.get("target_at"),
            safety_flags=req.get("safety_flags") or [],
            created_at=now,
            updated_at=now,
        )
        services.session.add(row)
        return {"id": row.id, "mock": True}

    @app.post("/api/v1/repair-contexts/{repair_id}/proposals")
    def repair_proposals(
        repair_id: str,
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        row = services.session.get(RepairContextRow, repair_id)
        if not row or row.owner_user_id != user.user_id:
            raise HTTPException(status_code=404, detail="repair context not found")
        action = str(req.get("action") or "customer_update_draft")
        approval = services.approvals.create(
            user,
            ApprovalCreateRequest(
                action_type="repair_copilot_proposal",
                provider="mock_repair_copilot",
                resource=repair_id,
                title=f"Approve mock {action}",
                proposed_content={
                    "action": action,
                    "repair_id": repair_id,
                    "draft": "Mock-only proposed action; no status is changed until approved.",
                },
                risk_level=RiskLevel.medium,
            ),
        )
        return {
            "mock": True,
            "approval": approval,
            "proposals": [
                "diagnostic_checklist",
                "missing_information_checklist",
                "customer_update_draft",
                "internal_note_draft",
                "parts_needed_list",
                "status_change_proposal",
                "follow_up_reminder",
                "safety_escalation",
            ],
        }

    @app.get("/api/v1/codex-task-records")
    def codex_tasks(
        user: UserIdentity = Depends(require_perm("assistant.chat")),
        services: RequestServices = Depends(get_services),
    ):
        rows = services.session.scalars(
            select(CodexTaskRecordRow).where(CodexTaskRecordRow.owner_user_id == user.user_id)
        ).all()
        return {
            "items": [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows],
            "mock": True,
        }

    @app.post("/api/v1/codex-task-records")
    def create_codex_task(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        now = datetime.now(UTC)
        row = CodexTaskRecordRow(
            id=make_id("codex"),
            owner_user_id=user.user_id,
            repository=str(req.get("repository") or "mock/repository"),
            objective=str(req.get("objective") or "Mock delegated task"),
            status=str(req.get("status") or "tracked"),
            started_at=req.get("started_at"),
            completion_at=req.get("completion_at"),
            blocked_reason=req.get("blocked_reason"),
            commit_sha=req.get("commit_sha"),
            pull_request_reference=req.get("pull_request_reference"),
            test_result=req.get("test_result"),
            next_owner_action=req.get("next_owner_action"),
            created_at=now,
            updated_at=now,
        )
        services.session.add(row)
        return {"id": row.id, "mock": True}

    def row_dict(row):
        return {c.name: getattr(row, c.name) for c in row.__table__.columns}

    def list_value(value: object) -> list[object]:
        return value if isinstance(value, list) else []

    def int_value(value: object, default: int) -> int:
        return value if isinstance(value, int) else default

    def float_value(value: object, default: float) -> float:
        return float(value) if isinstance(value, int | float | str) else default

    @app.post("/api/v1/memories")
    def create_memory(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import MemoryRow

        now = datetime.now(UTC)
        tags = list_value(req.get("tags"))
        body = str(req.get("body") or "")
        summary = str(req.get("summary") or "")
        row = MemoryRow(
            id=make_id("mem"),
            owner_user_id=user.user_id,
            title=str(req.get("title") or "Untitled memory")[:200],
            summary=summary[:500],
            body=body[:5000],
            category=str(req.get("category") or "business"),
            tags=tags,
            priority=int_value(req.get("priority"), 3),
            created_at=now,
            updated_at=now,
            expires_at=req.get("expires_at"),
            visibility=str(req.get("visibility") or "private"),
            confidence=float_value(req.get("confidence"), 1.0),
            related_memory_ids=list_value(req.get("related_memory_ids")),
            source=str(req.get("source") or "manual"),
            ai_generated=bool(req.get("ai_generated") or False),
            manual=bool(req.get("manual", True)),
            archived=False,
            deleted=False,
            pinned=bool(req.get("pinned") or False),
            favorite=bool(req.get("favorite") or False),
            search_vector=" ".join(
                [str(req.get("title") or ""), summary, body, " ".join(map(str, tags))]
            ).lower(),
        )
        services.session.add(row)
        services.audit.record(user, "memory", "created", resource_id=row.id)
        return row_dict(row)

    @app.get("/api/v1/memories")
    def list_memories(
        q: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        recent: bool = False,
        user: UserIdentity = Depends(require_perm("memories.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import MemoryRow

        stmt = select(MemoryRow).where(
            MemoryRow.owner_user_id == user.user_id, MemoryRow.deleted.is_(False)
        )
        if category:
            stmt = stmt.where(MemoryRow.category == category)
        rows = list(services.session.scalars(stmt).all())
        if tag:
            rows = [r for r in rows if tag in r.tags]
        if q:
            rows = [r for r in rows if q.lower() in r.search_vector]
        rows.sort(
            key=lambda r: (not r.pinned, not r.favorite, -r.priority, r.updated_at), reverse=False
        )
        if recent:
            rows = sorted(rows, key=lambda r: r.updated_at, reverse=True)[:10]
        return {"items": [row_dict(r) for r in rows], "mock": True}

    @app.get("/api/v1/memories/tags")
    def memory_tags(
        user: UserIdentity = Depends(require_perm("memories.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import MemoryRow

        tags = sorted(
            {
                t
                for r in services.session.scalars(
                    select(MemoryRow).where(
                        MemoryRow.owner_user_id == user.user_id, MemoryRow.deleted.is_(False)
                    )
                ).all()
                for t in r.tags
            }
        )
        return {"items": tags}

    @app.put("/api/v1/memories/{memory_id}")
    def update_memory(
        memory_id: str,
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import MemoryRow

        row = services.session.get(MemoryRow, memory_id)
        if not row or row.owner_user_id != user.user_id or row.deleted:
            raise NotFound("memory not found")
        for key in [
            "title",
            "summary",
            "body",
            "category",
            "tags",
            "priority",
            "expires_at",
            "visibility",
            "confidence",
            "related_memory_ids",
            "pinned",
            "favorite",
            "archived",
            "deleted",
        ]:
            if key in req:
                setattr(row, key, req[key])
        row.updated_at = datetime.now(UTC)
        row.search_vector = " ".join(
            [row.title, row.summary, row.body, " ".join(map(str, row.tags))]
        ).lower()
        services.audit.record(user, "memory", "updated", resource_id=row.id)
        return row_dict(row)

    @app.delete("/api/v1/memories/{memory_id}")
    def delete_memory(
        memory_id: str,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import MemoryRow

        row = services.session.get(MemoryRow, memory_id)
        if not row or row.owner_user_id != user.user_id:
            raise NotFound("memory not found")
        row.deleted = True
        row.updated_at = datetime.now(UTC)
        services.audit.record(user, "memory", "soft_deleted", resource_id=row.id)
        return {"deleted": True, "id": memory_id}

    @app.post("/api/v1/planning/tasks")
    def create_plan_task(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import PlanningTaskRow

        now = datetime.now(UTC)
        effort = int_value(req.get("effort_score"), 3)
        energy = int_value(req.get("energy_score"), 3)
        priority = int_value(req.get("priority"), 3)
        row = PlanningTaskRow(
            id=make_id("task"),
            owner_user_id=user.user_id,
            title=str(req.get("title") or "Untitled task")[:200],
            description=str(req.get("description") or ""),
            status=str(req.get("status") or "today"),
            priority=priority,
            manual_order=int_value(req.get("manual_order"), 100),
            ai_suggested_order=int_value(req.get("ai_suggested_order"), 100),
            time_estimate_minutes=int_value(req.get("time_estimate_minutes"), 15),
            effort_score=effort,
            energy_score=energy,
            focus_score=max(1, min(100, priority * 20 + energy * 8 - effort * 5)),
            deadline=req.get("deadline"),
            project_id=req.get("project_id"),
            tags=list_value(req.get("tags")),
            created_at=now,
            updated_at=now,
        )
        services.session.add(row)
        services.audit.record(user, "planning", "task_created", resource_id=row.id)
        return row_dict(row)

    @app.get("/api/v1/planning/tasks")
    def list_plan_tasks(
        status: str | None = None,
        user: UserIdentity = Depends(require_perm("planning.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import PlanningTaskRow

        stmt = select(PlanningTaskRow).where(PlanningTaskRow.owner_user_id == user.user_id)
        if status:
            stmt = stmt.where(PlanningTaskRow.status == status)
        rows = services.session.scalars(stmt).all()
        return {
            "items": [
                row_dict(r)
                for r in sorted(
                    rows, key=lambda r: (r.manual_order, -r.focus_score, r.deadline or datetime.max)
                )
            ]
        }

    @app.post("/api/v1/business-reminders")
    def create_business_reminder(
        req: dict[str, object],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import BusinessReminderRow

        now = datetime.now(UTC)
        scheduled = req.get("scheduled_at")
        row = BusinessReminderRow(
            id=make_id("rem"),
            owner_user_id=user.user_id,
            title=str(req.get("title") or "Reminder")[:200],
            body=str(req.get("body") or ""),
            reminder_type=str(req.get("reminder_type") or "one_time"),
            scheduled_at=scheduled,
            status="open",
            priority=int_value(req.get("priority"), 3),
            category=str(req.get("category") or "reminder"),
            related_task_id=req.get("related_task_id"),
            snooze_count=0,
            escalation_level=0,
            notification_ready=scheduled is None,
            created_at=now,
            updated_at=now,
        )
        services.session.add(row)
        services.audit.record(user, "reminder", "created", resource_id=row.id)
        return row_dict(row)

    @app.get("/api/v1/business-reminders")
    def list_business_reminders(
        status: str = "open",
        user: UserIdentity = Depends(require_perm("planning.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import BusinessReminderRow

        rows = services.session.scalars(
            select(BusinessReminderRow).where(
                BusinessReminderRow.owner_user_id == user.user_id,
                BusinessReminderRow.status == status,
            )
        ).all()
        return {"items": [row_dict(r) for r in rows], "notifications_mock_only": True}

    @app.post("/api/v1/business-reminders/{reminder_id}/{action}")
    def reminder_action(
        reminder_id: str,
        action: str,
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import BusinessReminderRow

        row = services.session.get(BusinessReminderRow, reminder_id)
        if not row or row.owner_user_id != user.user_id:
            raise NotFound("reminder not found")
        now = datetime.now(UTC)
        if action in {"complete", "dismiss"}:
            row.status = "completed" if action == "complete" else "dismissed"
            row.completed_at = now if action == "complete" else None
            row.dismissed_at = now if action == "dismiss" else None
        elif action == "snooze":
            row.snooze_count += 1
            row.status = "snoozed"
        elif action == "escalate":
            row.escalation_level += 1
        else:
            raise NotFound("reminder action not found")
        row.updated_at = now
        services.audit.record(user, "reminder", action, resource_id=row.id)
        return row_dict(row)

    @app.get("/api/v1/focus")
    def focus_mode(
        user: UserIdentity = Depends(require_perm("planning.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import PlanningTaskRow

        tasks = list(
            services.session.scalars(
                select(PlanningTaskRow).where(
                    PlanningTaskRow.owner_user_id == user.user_id,
                    PlanningTaskRow.status.in_(["today", "waiting", "blocked"]),
                )
            ).all()
        )
        ordered = sorted(tasks, key=lambda r: (r.status != "today", r.manual_order, -r.focus_score))
        return {
            "focus_now": ordered[0].title if ordered else None,
            "top_3_tasks": [row_dict(r) for r in ordered[:3]],
            "quick_win": next(
                (row_dict(r) for r in ordered if r.time_estimate_minutes <= 15), None
            ),
            "deep_work": next(
                (row_dict(r) for r in ordered if r.time_estimate_minutes >= 60), None
            ),
            "waiting_on": [row_dict(r) for r in tasks if r.status == "waiting"],
            "brain_dump": [],
            "parking_lot": [row_dict(r) for r in tasks if r.status == "deferred"],
            "recent_wins": [row_dict(r) for r in tasks if r.status == "completed"][-5:],
            "next_suggested_action": ordered[0].title if ordered else "Capture a brain dump item.",
        }

    @app.get("/api/v1/dashboard")
    def business_dashboard(
        user: UserIdentity = Depends(require_perm("dashboard.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import BusinessReminderRow, MemoryRow, PlanningTaskRow

        priorities = services.session.scalars(
            select(PlanningTaskRow).where(
                PlanningTaskRow.owner_user_id == user.user_id, PlanningTaskRow.status == "today"
            )
        ).all()
        reminders = services.session.scalars(
            select(BusinessReminderRow).where(
                BusinessReminderRow.owner_user_id == user.user_id,
                BusinessReminderRow.status == "open",
            )
        ).all()
        memories = services.session.scalars(
            select(MemoryRow)
            .where(MemoryRow.owner_user_id == user.user_id, MemoryRow.deleted.is_(False))
            .limit(5)
        ).all()
        approvals = services.approvals.list(user)
        focus_score = (
            int(sum([p.focus_score for p in priorities]) / max(len(priorities), 1))
            if priorities
            else 0
        )
        return {
            "today_priorities": [row_dict(r) for r in priorities],
            "open_reminders": [row_dict(r) for r in reminders],
            "recent_memories": [row_dict(r) for r in memories],
            "pending_approvals": [a for a in approvals if a.status == "pending"],
            "recent_activity": services.audit.list(user, None, 0, 5),
            "projects": sorted({r.project_id for r in priorities if r.project_id}),
            "business_focus_score": focus_score,
            "development_only": True,
        }

    @app.get("/api/v1/search")
    def assistant_search(
        q: str,
        user: UserIdentity = Depends(require_perm("search.read")),
        services: RequestServices = Depends(get_services),
    ):
        from nocturnix.persistence_models import BusinessReminderRow, MemoryRow, PlanningTaskRow

        query = q.lower()
        results = []
        searchable_tables = cast(
            Any,
            [
                ("memory", MemoryRow, ["title", "summary", "body"]),
                ("task", PlanningTaskRow, ["title", "description"]),
                ("reminder", BusinessReminderRow, ["title", "body"]),
            ],
        )
        for kind, cls, fields in searchable_tables:
            for r in services.session.scalars(
                select(cls).where(cls.owner_user_id == user.user_id)
            ).all():
                text = " ".join(str(getattr(r, f, "")) for f in fields).lower()
                if query in text:
                    results.append(
                        {
                            "type": kind,
                            "id": r.id,
                            "title": r.title,
                            "score": (10 if query in getattr(r, "title", "").lower() else 1)
                            + getattr(r, "priority", 1),
                        }
                    )
        return {"items": sorted(results, key=lambda x: x["score"], reverse=True)}

    @app.post("/api/v1/assistant/commands")
    def natural_command(
        req: dict[str, str],
        user: UserIdentity = Depends(require_csrf),
        services: RequestServices = Depends(get_services),
    ):
        text = (req.get("command") or "").strip()
        lower = text.lower()
        if lower.startswith("remember this"):
            return create_memory(
                {"title": text[:80], "body": text, "source": "natural_command"}, user, services
            )
        if lower.startswith("remind me"):
            return create_business_reminder(
                {"title": text[:120], "body": text, "reminder_type": "one_time"}, user, services
            )
        if lower.startswith("add task") or lower.startswith("brain dump"):
            return create_plan_task(
                {
                    "title": text[:120],
                    "description": text,
                    "status": "today" if lower.startswith("add task") else "deferred",
                },
                user,
                services,
            )
        if "waiting on" in lower:
            return list_plan_tasks("waiting", user, services)
        if "today" in lower:
            return business_dashboard(user, services)
        if lower.startswith("search memory"):
            return list_memories(
                text.removeprefix("search memory").strip(), None, None, False, user, services
            )
        return {
            "understood": False,
            "supported_commands": [
                "remember this",
                "remind me",
                "add task",
                "brain dump",
                "show today's tasks",
                "what am I waiting on",
                "search memory",
            ],
        }

    static_root = __import__("pathlib").Path(__file__).resolve().parents[1] / "static"
    app.mount("/static", StaticFiles(directory=static_root), name="static")

    @app.get("/")
    def ui_root():
        return FileResponse(static_root / "index.html")

    @app.get("/manifest.webmanifest")
    def manifest():
        return FileResponse(static_root / "manifest.webmanifest")

    @app.get("/service-worker.js")
    def service_worker(response: Response):
        response.headers["Cache-Control"] = "no-store"
        return FileResponse(static_root / "service-worker.js")

    return app

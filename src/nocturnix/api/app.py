from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager
from time import monotonic
from uuid import uuid4
from weakref import finalize

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
from nocturnix.repositories.sql import (
    SqlApprovalRepository,
    SqlAuditRepository,
    SqlConversationRepository,
    SqlMessageRepository,
    SqlPreferenceRepository,
    SqlRepairIntakeRepository,
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
        allow_headers=["Content-Type", "X-Nocturnix-Dev-User", "X-Request-ID"],
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
            "auth_mode": "mock-development-only",
        }

    @app.get("/api/v1/status")
    def status(
        container: AppContainer = Depends(get_container), user: UserIdentity = Depends(current_user)
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
            "retention_configured": True,
            "ready": True,
            "user_id": user.user_id,
        }

    @app.post("/api/v1/chat")
    def chat(
        req: ChatRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
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
        user: UserIdentity = Depends(current_user),
    ):
        services.audit.record(user, "knowledge", "searched")
        results, placeholder = services.container.knowledge.search(req.query, req.limit)
        return KnowledgeSearchResponse(results=results, placeholder=placeholder)

    @app.post("/api/v1/repair-intakes")
    def repair_intake(
        req: RepairIntakeRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
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
        user: UserIdentity = Depends(current_user),
    ):
        return services.approvals.create(user, req)

    @app.get("/api/v1/approvals")
    def list_approvals(
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
    ):
        return {"items": services.approvals.list(user)}

    @app.get("/api/v1/approvals/{approval_id}")
    def get_approval(
        approval_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
    ):
        return services.approvals.get(user, approval_id)

    @app.post("/api/v1/approvals/{approval_id}/approve")
    def approve(
        approval_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
    ):
        return services.approvals.approve(user, approval_id)

    @app.post("/api/v1/approvals/{approval_id}/reject")
    def reject(
        approval_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
    ):
        return services.approvals.reject(user, approval_id)

    @app.get("/api/v1/audit")
    def audit(
        offset: int = 0,
        limit: int = 20,
        category: str | None = None,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
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
    def list_email(user: UserIdentity = Depends(current_user)):
        return {"mock": True, "items": email_messages}

    @app.get("/api/v1/mock/email/messages/{message_id}")
    def get_email(message_id: str, user: UserIdentity = Depends(current_user)):
        return next(
            (m for m in email_messages if m["id"] == message_id),
            (_ for _ in ()).throw(NotFound("email not found")),
        )

    @app.post("/api/v1/mock/email/messages/{message_id}/summarize")
    def summarize_email(message_id: str, user: UserIdentity = Depends(current_user)):
        return {
            "mock": True,
            "message_id": message_id,
            "summary": "Fictional email summary. Gmail is not connected.",
        }

    @app.post("/api/v1/mock/email/messages/{message_id}/draft-proposal")
    def email_draft(
        message_id: str,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
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
    def list_calendar(user: UserIdentity = Depends(current_user)):
        return {"mock": True, "items": calendar_events}

    @app.post("/api/v1/mock/calendar/event-proposals")
    def calendar_proposal(
        req: CalendarProposal,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
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
        user: UserIdentity = Depends(current_user),
    ):
        return services.preferences.get(user)

    @app.put("/api/v1/preferences")
    def put_preferences(
        req: PreferencesUpdateRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
    ):
        return services.preferences.update(user, req)

    @app.post("/api/v1/retention/cleanup")
    def retention_cleanup(
        req: RetentionCleanupRequest,
        services: RequestServices = Depends(get_services),
        user: UserIdentity = Depends(current_user),
    ):
        return services.retention.cleanup(user, dry_run=req.dry_run)

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

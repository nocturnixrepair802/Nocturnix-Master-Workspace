from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from nocturnix.assistant.coding_service import CodingAssistantService, ConversationAccessError
from nocturnix.assistant.exceptions import AssistantTaskNotFoundError
from nocturnix.assistant.openai_provider import CodingAssistantProvider, CodingProviderError
from nocturnix.assistant.provider_factory import provider_name
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.assistant.repository_access import RepositoryAccessError
from nocturnix.assistant.web_models import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantHealthResponse,
    AssistantResultResponse,
    AssistantResultsResponse,
    AssistantTaskResponse,
)
from nocturnix.db import database_ready
from nocturnix.models import UserIdentity


def create_assistant_web_router(
    get_services: Callable[..., object],
    auth_identity: Callable[..., UserIdentity],
    require_csrf: Callable[..., UserIdentity],
) -> APIRouter:
    router = APIRouter()
    static_root = Path(__file__).resolve().parents[1] / "static"

    @router.get("/assistant", include_in_schema=False)
    def assistant_page() -> FileResponse:
        return FileResponse(static_root / "coding-assistant.html")

    @router.get("/api/assistant/health", response_model=AssistantHealthResponse)
    def health(request: Request) -> AssistantHealthResponse:
        settings = request.app.state.container.settings
        provider: CodingAssistantProvider | None = request.app.state.coding_provider
        return AssistantHealthResponse(
            status="ok",
            service="nocturnix-development-assistant",
            provider=provider_name(provider) if provider is not None else settings.coding_provider,
            model=provider.model if provider is not None else settings.openai_model,
            openai_configured=bool(
                settings.openai_enabled
                and settings.external_providers_enabled
                and settings.openai_api_key
                and settings.openai_model
            ),
            database_configured=database_ready(settings.database_url),
        )

    @router.post("/api/assistant/chat", response_model=AssistantChatResponse)
    def chat(
        payload: AssistantChatRequest,
        request: Request,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantChatResponse:
        provider: CodingAssistantProvider | None = request.app.state.coding_provider
        if provider is None:
            raise HTTPException(status_code=503, detail="Coding provider is not configured.")
        try:
            return CodingAssistantService(
                services.session,
                provider,
                services.container.settings.conversation_retention_days,
            ).chat(user.user_id, payload)
        except CodingProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_detail) from exc
        except RepositoryAccessError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ConversationAccessError as exc:
            raise HTTPException(status_code=404, detail="Conversation not found.") from exc

    @router.get("/api/assistant/tasks/{task_id}", response_model=AssistantTaskResponse)
    def task(
        task_id: str,
        services=Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ) -> AssistantTaskResponse:
        repository = AssistantTaskRepository(services.session)
        try:
            row = repository.get_task(task_id, user.user_id)
        except AssistantTaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Assistant task not found.") from exc
        return AssistantTaskResponse.model_validate(row, from_attributes=True)

    @router.get(
        "/api/assistant/tasks/{task_id}/results",
        response_model=AssistantResultsResponse,
    )
    def results(
        task_id: str,
        services=Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ) -> AssistantResultsResponse:
        repository = AssistantTaskRepository(services.session)
        try:
            rows = repository.list_results(task_id, owner_user_id=user.user_id)
        except AssistantTaskNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Assistant task not found.") from exc
        return AssistantResultsResponse(
            items=[
                AssistantResultResponse.model_validate(row, from_attributes=True) for row in rows
            ]
        )

    return router


__all__ = ["create_assistant_web_router"]

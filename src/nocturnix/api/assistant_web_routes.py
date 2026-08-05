from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from nocturnix.assistant.coding_service import CodingAssistantService, ConversationAccessError
from nocturnix.assistant.exceptions import AssistantTaskNotFoundError
from nocturnix.assistant.openai_provider import CodingAssistantProvider, CodingProviderError
from nocturnix.assistant.repository_access import RepositoryAccessError, RepositoryAccessService
from nocturnix.assistant.provider_factory import provider_name
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.assistant.web_models import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantHealthResponse,
    AssistantResultResponse,
    AssistantResultsResponse,
    AssistantTaskResponse,
)
from nocturnix.assistant.repository_models import (
    RepositoryFileResponse,
    RepositoryFilesResponse,
    RepositorySearchRequest,
    RepositorySearchResponse,
    RepositoryStatusResponse,
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


    def repository_service(request: Request) -> RepositoryAccessService:
        settings = request.app.state.container.settings
        return RepositoryAccessService(
            settings.safe_repository_root,
            settings.repository_max_file_bytes,
            settings.repository_search_result_limit,
        )

    @router.get(
        "/api/assistant/repository/status",
        response_model=RepositoryStatusResponse,
    )
    def repository_status(
        service: RepositoryAccessService = Depends(repository_service),
        user: UserIdentity = Depends(auth_identity),
    ) -> RepositoryStatusResponse:
        return service.status()

    @router.get(
        "/api/assistant/repository/files",
        response_model=RepositoryFilesResponse,
    )
    def repository_files(
        prefix: str | None = None,
        extension: str | None = None,
        limit: int = 100,
        offset: int = 0,
        service: RepositoryAccessService = Depends(repository_service),
        user: UserIdentity = Depends(auth_identity),
    ) -> RepositoryFilesResponse:
        try:
            return service.list_files(
                prefix=prefix,
                extension=extension,
                limit=max(1, min(limit, 500)),
                offset=max(0, offset),
            )
        except RepositoryAccessError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    @router.post(
        "/api/assistant/repository/search",
        response_model=RepositorySearchResponse,
    )
    def repository_search(
        payload: RepositorySearchRequest,
        service: RepositoryAccessService = Depends(repository_service),
        user: UserIdentity = Depends(auth_identity),
    ) -> RepositorySearchResponse:
        return service.search(
            query=payload.query,
            search_content=payload.search_content,
            extensions=payload.extensions,
            limit=payload.limit,
        )

    @router.get(
        "/api/assistant/repository/file",
        response_model=RepositoryFileResponse,
    )
    def repository_file(
        path: str,
        service: RepositoryAccessService = Depends(repository_service),
        user: UserIdentity = Depends(auth_identity),
    ) -> RepositoryFileResponse:
        try:
            return service.read_file(path)
        except RepositoryAccessError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

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
            settings = services.container.settings
            repository = RepositoryAccessService(
                settings.safe_repository_root,
                settings.repository_max_file_bytes,
                settings.repository_search_result_limit,
            )
            return CodingAssistantService(
                services.session,
                provider,
                services.container.settings.conversation_retention_days,
                repository,
            ).chat(user.user_id, payload)
        except RepositoryAccessError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        except CodingProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_detail) from exc
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

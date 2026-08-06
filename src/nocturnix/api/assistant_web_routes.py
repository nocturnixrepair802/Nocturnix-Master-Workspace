from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from nocturnix.assistant.coding_service import CodingAssistantService, ConversationAccessError
from nocturnix.assistant.exceptions import AssistantTaskNotFoundError
from nocturnix.assistant.openai_provider import CodingAssistantProvider, CodingProviderError
from nocturnix.assistant.provider_factory import provider_name
from nocturnix.assistant.reference_analysis import analyze_repository_references
from nocturnix.assistant.repository_access import RepositoryAccessError
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.assistant.symbol_graph import (
    SymbolGraph,
    build_project_symbol_graph,
    symbol_graph_for_symbol,
)
from nocturnix.assistant.web_models import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantHealthResponse,
    AssistantRepositoryReferenceItem,
    AssistantRepositoryReferencesRequest,
    AssistantRepositoryReferencesResponse,
    AssistantResultResponse,
    AssistantResultsResponse,
    AssistantSymbolEdge,
    AssistantSymbolGraphRequest,
    AssistantSymbolGraphResponse,
    AssistantSymbolNode,
    AssistantSymbolNodeResponse,
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

    @router.post(
        "/api/assistant/repository/references",
        response_model=AssistantRepositoryReferencesResponse,
    )
    def repository_references(
        payload: AssistantRepositoryReferencesRequest,
        request: Request,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantRepositoryReferencesResponse:
        try:
            items = analyze_repository_references(
                Path(payload.repository_root),
                payload.symbol,
                payload.extensions or None,
                payload.max_results,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return AssistantRepositoryReferencesResponse(
            items=[
                AssistantRepositoryReferenceItem(
                    path=item.path,
                    line_number=item.line_number,
                    reference_type=item.reference_type,
                    excerpt=item.excerpt,
                )
                for item in items
            ]
        )

    @router.get(
        "/api/assistant/repository/symbols",
        response_model=AssistantSymbolGraphResponse,
    )
    def repository_symbols(
        repository_root: str,
        extensions: list[str] | None = None,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantSymbolGraphResponse:
        try:
            graph = build_project_symbol_graph(
                Path(repository_root),
                extensions=extensions,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return AssistantSymbolGraphResponse(
            root=graph.root,
            nodes=[AssistantSymbolNode(**node.__dict__) for node in graph.nodes],
            edges=[AssistantSymbolEdge(**edge.__dict__) for edge in graph.edges],
        )

    @router.get(
        "/api/assistant/repository/symbols/{qualified_name}",
        response_model=AssistantSymbolNodeResponse,
    )
    def repository_symbol(
        qualified_name: str,
        repository_root: str,
        extensions: list[str] | None = None,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantSymbolNodeResponse:
        try:
            graph = build_project_symbol_graph(
                Path(repository_root),
                extensions=extensions,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        node = next(
            (node for node in graph.nodes if node.qualified_name == qualified_name),
            None,
        )
        if node is None:
            raise HTTPException(status_code=404, detail="Symbol not found.")

        outgoing_edges = [
            AssistantSymbolEdge(**edge.__dict__)
            for edge in graph.edges
            if edge.source == node.qualified_name
        ]
        incoming_edges = [
            AssistantSymbolEdge(**edge.__dict__)
            for edge in graph.edges
            if edge.target == node.qualified_name
        ]
        return AssistantSymbolNodeResponse(
            node=AssistantSymbolNode(**node.__dict__),
            outgoing_edges=outgoing_edges,
            incoming_edges=incoming_edges,
        )

    @router.post(
        "/api/assistant/repository/symbol-graph",
        response_model=AssistantSymbolGraphResponse,
    )
    def repository_symbol_graph(
        payload: AssistantSymbolGraphRequest,
        request: Request,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantSymbolGraphResponse:
        try:
            graph = build_project_symbol_graph(
                Path(payload.repository_root),
                extensions=payload.extensions or None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if payload.symbol:
            try:
                graph = symbol_graph_for_symbol(graph, payload.symbol, payload.depth, payload.limit)
            except KeyError:
                raise HTTPException(status_code=404, detail="Symbol not found.") from None

        return AssistantSymbolGraphResponse(
            root=graph.root,
            nodes=[AssistantSymbolNode(**node.__dict__) for node in graph.nodes],
            edges=[AssistantSymbolEdge(**edge.__dict__) for edge in graph.edges],
        )

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

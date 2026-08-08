from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from nocturnix.assistant.coding_service import CodingAssistantService, ConversationAccessError
from nocturnix.assistant.exceptions import AssistantTaskNotFoundError
from nocturnix.assistant.openai_provider import CodingAssistantProvider, CodingProviderError
from nocturnix.assistant.patch_apply import (
    PatchApplyError,
    PatchApplyService,
)
from nocturnix.assistant.patch_models import PatchProposalError
from nocturnix.assistant.patch_proposals import propose_patch
from nocturnix.assistant.provider_factory import provider_name
from nocturnix.assistant.reference_analysis import analyze_repository_references
from nocturnix.assistant.repositories import AssistantTaskRepository
from nocturnix.assistant.repository_access import RepositoryAccessError, RepositoryAccessService
from nocturnix.assistant.repository_models import (
    RepositoryFileResponse,
    RepositoryFilesResponse,
    RepositorySearchRequest,
    RepositorySearchResponse,
    RepositoryStatusResponse,
)
from nocturnix.assistant.service import AssistantTaskService
from nocturnix.assistant.symbol_graph import (
    build_project_symbol_graph,
    symbol_graph_for_symbol,
)
from nocturnix.assistant.web_models import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantHealthResponse,
    AssistantPatchApplyRequest,
    AssistantPatchApplyResponse,
    AssistantPatchProposalHistoryItem,
    AssistantPatchProposalHistoryResponse,
    AssistantPatchProposalRequest,
    AssistantPatchProposalResponse,
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
from nocturnix.security.auth import AuthorizationService


def create_assistant_web_router(
    get_services: Callable[..., object],
    auth_identity: Callable[..., UserIdentity],
    require_csrf: Callable[..., UserIdentity],
) -> APIRouter:
    router = APIRouter()
    static_root = Path(__file__).resolve().parents[1] / "static"

    def require_assistant_permission(
        services,
        user: UserIdentity,
    ) -> None:
        AuthorizationService(services.session).require(
            user,
            "assistant.chat",
        )

    @router.post(
        "/api/assistant/repository/propose-patch",
        response_model=AssistantPatchProposalResponse,
    )
    def repository_propose_patch(
        payload: AssistantPatchProposalRequest,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantPatchProposalResponse:
        require_assistant_permission(
            services,
            user,
        )

        default_repository_root = Path(__file__).resolve().parents[3]

        repository_root = (
            Path(payload.repository_root)
            if payload.repository_root is not None
            else default_repository_root
        )

        try:
            proposal = propose_patch(
                repository_root=repository_root,
                instruction=payload.instruction,
                selected_files=payload.selected_files,
                title=payload.title,
            )
        except PatchProposalError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        task_service = AssistantTaskService(AssistantTaskRepository(services.session))

        task = task_service.create_task(
            owner_user_id=user.user_id,
            task_type="patch_proposal",
            title=proposal.title,
            instructions=payload.instruction,
            input_data={
                "repository_root": str(repository_root.resolve()),
                "selected_files": proposal.affected_files,
            },
        )

        task_service.start_task(
            task.id,
            owner_user_id=user.user_id,
        )

        persisted_proposal = task_service.save_patch_proposal(
            owner_user_id=user.user_id,
            task_id=task.id,
            repository_root=str(repository_root.resolve()),
            target_file=proposal.affected_files[0],
            instructions=payload.instruction,
            unified_diff=proposal.unified_diff,
            original_sha256=proposal.original_sha256,
            proposed_sha256=proposal.proposed_sha256,
            metadata_json={
                "title": proposal.title,
                "summary": proposal.summary,
                "affected_files": proposal.affected_files,
                "warnings": proposal.warnings,
                "generated_locally": proposal.generated_locally,
                "applied": proposal.applied,
            },
        )

        task_service.complete_task(
            task.id,
            result_summary="Patch proposal generated and persisted.",
            owner_user_id=user.user_id,
        )

        return AssistantPatchProposalResponse(
            proposal_id=persisted_proposal.id,
            task_id=task.id,
            title=proposal.title,
            summary=proposal.summary,
            affected_files=proposal.affected_files,
            unified_diff=proposal.unified_diff,
            warnings=proposal.warnings,
            generated_locally=proposal.generated_locally,
            applied=proposal.applied,
        )

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
            settings = request.app.state.container.settings
            repository = repository_service(request)

            return CodingAssistantService(
                services.session,
                provider,
                settings.conversation_retention_days,
                repository,
            ).chat(user.user_id, payload)
        except RepositoryAccessError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=str(exc),
            ) from exc
        except CodingProviderError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=exc.public_detail,
            ) from exc
        except ConversationAccessError as exc:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            ) from exc

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
        "/api/assistant/patches/{proposal_id}",
        response_model=AssistantPatchProposalHistoryItem,
    )
    def patch_proposal(
        proposal_id: str,
        services=Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ) -> AssistantPatchProposalHistoryItem:
        require_assistant_permission(
            services,
            user,
        )

        task_service = AssistantTaskService(AssistantTaskRepository(services.session))

        try:
            proposal = task_service.get_patch_proposal(
                proposal_id,
                owner_user_id=user.user_id,
            )
        except LookupError as exc:
            raise HTTPException(
                status_code=404,
                detail="Patch proposal not found.",
            ) from exc

        return AssistantPatchProposalHistoryItem(
            id=proposal.id,
            task_id=proposal.task_id,
            conversation_id=proposal.conversation_id,
            repository_root=proposal.repository_root,
            target_file=proposal.target_file,
            instructions=proposal.instructions,
            unified_diff=proposal.unified_diff,
            original_sha256=proposal.original_sha256,
            proposed_sha256=proposal.proposed_sha256,
            metadata_json=proposal.metadata_json,
            created_at=proposal.created_at,
        )

    @router.get(
        "/api/assistant/tasks/{task_id}/patches",
        response_model=AssistantPatchProposalHistoryResponse,
    )
    def task_patch_proposals(
        task_id: str,
        services=Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ) -> AssistantPatchProposalHistoryResponse:
        require_assistant_permission(
            services,
            user,
        )

        task_service = AssistantTaskService(AssistantTaskRepository(services.session))

        try:
            task_service.get_task(
                task_id,
                owner_user_id=user.user_id,
            )
        except AssistantTaskNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail="Assistant task not found.",
            ) from exc

        proposals = task_service.list_patch_proposals(
            owner_user_id=user.user_id,
            task_id=task_id,
        )

        return AssistantPatchProposalHistoryResponse(
            items=[
                AssistantPatchProposalHistoryItem(
                    id=proposal.id,
                    task_id=proposal.task_id,
                    conversation_id=proposal.conversation_id,
                    repository_root=proposal.repository_root,
                    target_file=proposal.target_file,
                    instructions=proposal.instructions,
                    unified_diff=proposal.unified_diff,
                    original_sha256=proposal.original_sha256,
                    proposed_sha256=proposal.proposed_sha256,
                    metadata_json=proposal.metadata_json,
                    created_at=proposal.created_at,
                )
                for proposal in proposals
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

    @router.post(
        "/api/assistant/patches/{proposal_id}/apply",
        response_model=AssistantPatchApplyResponse,
    )
    def apply_patch_proposal(
        proposal_id: str,
        payload: AssistantPatchApplyRequest,
        services=Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ) -> AssistantPatchApplyResponse:
        require_assistant_permission(
            services,
            user,
        )

        if not payload.confirm:
            raise HTTPException(
                status_code=400,
                detail="Patch application requires explicit confirmation.",
            )

        task_service = AssistantTaskService(AssistantTaskRepository(services.session))

        apply_service = PatchApplyService(task_service)

        try:
            proposal = apply_service.apply(
                proposal_id,
                owner_user_id=user.user_id,
                applied_by_user_id=user.user_id,
            )
        except LookupError as exc:
            raise HTTPException(
                status_code=404,
                detail="Patch proposal not found.",
            ) from exc
        except PatchApplyError as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

        return AssistantPatchApplyResponse(
            proposal_id=proposal.id,
            task_id=proposal.task_id,
            status=proposal.status,
            target_file=proposal.target_file,
            applied_at=proposal.applied_at,
            applied_by_user_id=proposal.applied_by_user_id,
            failure_reason=proposal.failure_reason,
        )

    return router

   
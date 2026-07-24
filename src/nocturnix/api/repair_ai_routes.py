from __future__ import annotations

from collections.abc import Callable
from time import monotonic
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import Field

from nocturnix.models import StrictModel, UserIdentity
from nocturnix.openai_provider_errors import classify_openai_exception
from nocturnix.openai_repair_agent import OpenAIRepairAgent
from nocturnix.repair_ai_tools import RepairAssistantTools
from nocturnix.repair_confirmation_store import (
    RepairConfirmationConsumed,
    RepairConfirmationExpired,
    RepairConfirmationNotFound,
    RepairConfirmationStore,
    SqlRepairConfirmationStore,
)


class RepairToolExecuteRequest(StrictModel):
    tool_name: str = Field(min_length=1, max_length=120)
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class RepairToolExecuteResponse(StrictModel):
    tool_name: str
    confirmed: bool
    result: Any


class RepairAgentChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=4000)
    previous_response_id: str | None = Field(default=None, max_length=200)
    confirmation_id: str | None = Field(default=None, max_length=80)


class RepairAgentChatResponse(StrictModel):
    response: str
    response_id: str | None = None
    proposed_actions: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)


def create_repair_ai_router(
    get_services: Callable[..., Any],
    auth_identity: Callable[..., UserIdentity],
    require_csrf: Callable[..., UserIdentity],
    confirmation_store: RepairConfirmationStore | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ai/repair-tools", tags=["repair-ai-tools"])

    @router.get("")
    def list_tools(
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(auth_identity),
    ):
        del user
        return RepairAssistantTools(services.repair_domain).openai_tools()

    @router.post("/execute", response_model=RepairToolExecuteResponse)
    def execute_tool(
        req: RepairToolExecuteRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        result = RepairAssistantTools(services.repair_domain).execute(
            owner_user_id=user.user_id,
            tool_name=req.tool_name,
            arguments=req.arguments,
            confirmed=req.confirmed,
        )
        services.audit.record(
            user,
            "repair_ai_tool",
            req.tool_name,
            metadata={"confirmed": req.confirmed},
        )
        return {
            "tool_name": req.tool_name,
            "confirmed": req.confirmed,
            "result": result,
        }

    @router.post("/chat", response_model=RepairAgentChatResponse)
    def repair_agent_chat(
        req: RepairAgentChatRequest,
        services: Any = Depends(get_services),
        user: UserIdentity = Depends(require_csrf),
    ):
        settings = services.container.settings
        if not settings.openai_enabled or not settings.external_providers_enabled:
            raise HTTPException(status_code=503, detail="OpenAI repair agent is not enabled")
        if not settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OpenAI API key is not configured")

        confirmations = confirmation_store or SqlRepairConfirmationStore(services.session)
        previous_response_id = req.previous_response_id
        confirmed_actions: set[str] = set()
        if req.confirmation_id:
            try:
                pending = confirmations.consume(
                    confirmation_id=req.confirmation_id,
                    owner_user_id=user.user_id,
                )
            except RepairConfirmationNotFound as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except RepairConfirmationExpired as exc:
                raise HTTPException(status_code=410, detail=str(exc)) from exc
            except RepairConfirmationConsumed as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            previous_response_id = pending.previous_response_id
            confirmed_actions.add(pending.action_key)

        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=2,
        )
        agent = OpenAIRepairAgent(
            client,
            services.repair_domain,
            model=settings.openai_model,
            max_tool_rounds=settings.openai_max_tool_rounds,
        )
        started_at = monotonic()
        try:
            result = agent.run(
                owner_user_id=user.user_id,
                message=req.message,
                previous_response_id=previous_response_id,
                confirmed_actions=confirmed_actions,
            )
        except Exception as exc:
            provider_failure = classify_openai_exception(exc)
            if provider_failure is None:
                raise
            services.audit.record(
                user,
                "repair_ai_agent",
                "provider_failure",
                metadata={
                    "model": settings.openai_model,
                    "category": provider_failure.category,
                    "retryable": provider_failure.retryable,
                    "request_id": provider_failure.request_id,
                    "latency_ms": int((monotonic() - started_at) * 1000),
                    "confirmation_used": bool(req.confirmation_id),
                },
            )
            raise HTTPException(
                status_code=provider_failure.status_code,
                detail=provider_failure.public_detail,
                headers=({"Retry-After": "2"} if provider_failure.status_code == 429 else None),
            ) from exc

        proposed_actions: list[dict[str, Any]] = []
        if result.response_id:
            for action in result.proposed_actions:
                pending = confirmations.create(
                    owner_user_id=user.user_id,
                    previous_response_id=result.response_id,
                    tool_name=action.tool_name,
                    arguments=action.arguments,
                    action_key=agent.action_key(action.tool_name, action.arguments),
                )
                proposed_actions.append(
                    {
                        "tool_name": action.tool_name,
                        "arguments": action.arguments,
                        "confirmation_id": pending.id,
                        "expires_at": pending.expires_at.isoformat(),
                    }
                )

        services.audit.record(
            user,
            "repair_ai_agent",
            "chat",
            metadata={
                "model": settings.openai_model,
                "confirmation_used": bool(req.confirmation_id),
                "confirmation_store": "memory" if confirmation_store else "sql",
                "proposed_action_count": len(proposed_actions),
                "tool_result_count": len(result.tool_results),
                "response_id": result.response_id,
                "latency_ms": int((monotonic() - started_at) * 1000),
            },
        )
        return {
            "response": result.text,
            "response_id": result.response_id,
            "proposed_actions": proposed_actions,
            "tool_results": result.tool_results,
        }

    return router


__all__ = ["create_repair_ai_router"]

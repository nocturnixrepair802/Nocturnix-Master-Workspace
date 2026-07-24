from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import Field

from nocturnix.models import StrictModel, UserIdentity
from nocturnix.repair_ai_tools import RepairAssistantTools


class RepairToolExecuteRequest(StrictModel):
    tool_name: str = Field(min_length=1, max_length=120)
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class RepairToolExecuteResponse(StrictModel):
    tool_name: str
    confirmed: bool
    result: Any


def create_repair_ai_router(
    get_services: Callable[..., Any],
    auth_identity: Callable[..., UserIdentity],
    require_csrf: Callable[..., UserIdentity],
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

    return router


__all__ = ["create_repair_ai_router"]

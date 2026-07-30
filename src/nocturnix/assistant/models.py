from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssistantTaskStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssistantTaskType(StrEnum):
    GENERAL = "general"
    REPAIR = "repair"
    WEB_RESEARCH = "web_research"
    SPREADSHEET = "spreadsheet"
    DOCUMENT = "document"
    EMAIL = "email"
    CALENDAR = "calendar"


class AssistantTool(StrEnum):
    REPAIR = "repair"
    WEB = "web"
    SPREADSHEET = "spreadsheet"
    DOCUMENT = "document"
    EMAIL = "email"
    CALENDAR = "calendar"


class AssistantTaskCreate(BaseModel):
    task_type: AssistantTaskType
    title: str = Field(min_length=1, max_length=255)
    instructions: str = Field(min_length=1)
    conversation_id: UUID | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)


class AssistantTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID
    conversation_id: UUID | None = None
    task_type: str
    title: str
    instructions: str
    status: str
    progress_percent: int
    input_data: dict[str, Any] | None = None
    result_summary: str | None = None

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=20_000)
    conversation_id: str | None = Field(default=None, max_length=64)
    project_context: str | None = Field(default=None, max_length=40_000)
    selected_files: list[str] = Field(default_factory=list, max_length=100)
    task_type: str = Field(default="coding_assistance", pattern="^coding_assistance$")

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class AssistantChatResponse(BaseModel):
    task_id: str
    conversation_id: str
    status: str
    answer: str
    result_id: str
    model: str
    completed_at: datetime


class AssistantHealthResponse(BaseModel):
    status: str
    service: str
    openai_configured: bool
    database_configured: bool


class AssistantTaskResponse(BaseModel):
    id: str
    conversation_id: str | None
    task_type: str
    title: str
    status: str
    progress_percent: int
    result_summary: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class AssistantResultResponse(BaseModel):
    id: str
    task_id: str
    result_type: str
    title: str
    summary: str
    content: dict[str, object]
    media_type: str | None
    created_at: datetime


class AssistantResultsResponse(BaseModel):
    items: list[AssistantResultResponse]

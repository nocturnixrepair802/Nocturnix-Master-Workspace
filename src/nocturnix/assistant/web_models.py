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
    provider: str
    model: str
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


class AssistantRepositoryReferenceItem(BaseModel):
    path: str
    line_number: int
    reference_type: str
    excerpt: str


class AssistantRepositoryReferencesRequest(BaseModel):
    repository_root: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    extensions: list[str] = Field(default_factory=list)
    max_results: int = Field(default=50, ge=1, le=200)


class AssistantRepositoryReferencesResponse(BaseModel):
    items: list[AssistantRepositoryReferenceItem]


class AssistantSymbolNode(BaseModel):
    name: str
    qualified_name: str
    path: str
    line_number: int
    node_type: str


class AssistantSymbolEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    path: str
    line_number: int


class AssistantSymbolGraphRequest(BaseModel):
    repository_root: str = Field(min_length=1)
    symbol: str | None = None
    depth: int = Field(default=1, ge=0, le=5)
    limit: int = Field(default=100, ge=1, le=500)
    extensions: list[str] = Field(default_factory=list)


class AssistantSymbolGraphResponse(BaseModel):
    root: str | None
    nodes: list[AssistantSymbolNode]
    edges: list[AssistantSymbolEdge]


class AssistantSymbolNodeResponse(BaseModel):
    node: AssistantSymbolNode
    outgoing_edges: list[AssistantSymbolEdge]
    incoming_edges: list[AssistantSymbolEdge]


class AssistantPatchProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instruction: str = Field(
        min_length=1,
        max_length=10_000,
    )
    selected_files: list[str] = Field(
        min_length=1,
        max_length=10,
    )
    title: str | None = Field(
        default=None,
        max_length=200,
    )
    repository_root: str | None = Field(
        default=None,
        min_length=1,
    )

    @field_validator("instruction")
    @classmethod
    def instruction_not_blank(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("instruction must not be blank")

        return normalized

    @field_validator("selected_files")
    @classmethod
    def selected_files_not_blank(
        cls,
        value: list[str],
    ) -> list[str]:
        normalized_files = [file_path.strip() for file_path in value]

        if any(not file_path for file_path in normalized_files):
            raise ValueError("selected_files must not contain blank paths")

        return normalized_files


class AssistantPatchProposalFileResponse(BaseModel):
    path: str
    unified_diff: str
    original_sha256: str
    proposed_sha256: str


class AssistantPatchProposalResponse(BaseModel):
    proposal_id: str
    task_id: str
    title: str
    summary: str
    affected_files: list[str]
    unified_diff: str
    files: list[AssistantPatchProposalFileResponse]
    warnings: list[str]
    generated_locally: bool
    applied: bool


class AssistantPatchProposalHistoryItem(BaseModel):
    id: str
    task_id: str
    conversation_id: str | None
    repository_root: str
    target_file: str
    instructions: str
    unified_diff: str
    original_sha256: str
    proposed_sha256: str
    files: list[AssistantPatchProposalFileResponse]
    metadata_json: dict[str, object]
    status: str
    applied_at: datetime | None
    applied_by_user_id: str | None
    failure_reason: str | None
    created_at: datetime


class AssistantPatchProposalHistoryResponse(BaseModel):
    items: list[AssistantPatchProposalHistoryItem]


class AssistantPatchApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool = True


class AssistantPatchApplyResponse(BaseModel):
    proposal_id: str
    task_id: str
    status: str
    target_file: str
    applied_at: datetime | None
    applied_by_user_id: str | None
    failure_reason: str | None

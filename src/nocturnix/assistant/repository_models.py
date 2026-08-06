from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ----------------------------------------------------------------------
# Repository browser models
# ----------------------------------------------------------------------


class RepositoryFileItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    extension: str
    size_bytes: int


class RepositoryFileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    extension: str
    size_bytes: int
    content: str
    truncated: bool = False


class RepositoryFilesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RepositoryFileItem]
    total: int
    limit: int
    offset: int


class RepositorySearchMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    match_type: str
    excerpt: str
    line_number: int | None = None
    order: int = 0


class RepositorySearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        min_length=1,
        max_length=500,
    )
    search_content: bool = True
    extensions: list[str] = Field(
        default_factory=list,
        max_length=50,
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        le=500,
    )

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("query must not be blank")

        return normalized

    @field_validator("selected_files")
    @classmethod
    def validate_selected_files(cls, value: list[str]) -> list[str]:
        if len(value) > 100:
            raise ValueError("selected_files cannot contain more than 100 file paths")
        if any(not file_path or not file_path.strip() for file_path in value):
            raise ValueError("selected_files must not contain empty file paths")
        return [file_path.strip() for file_path in value]

class RepositorySearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    items: list[RepositorySearchMatch]
    limit: int

class RepositoryContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

class RepositoryStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    root_name: str
    indexed_file_count: int
    ignored_path_count: int
    max_file_bytes: int


# ----------------------------------------------------------------------
# Repository context models
# ----------------------------------------------------------------------


class RepositoryFileReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        min_length=1,
        description="A repository-relative file path using forward slashes.",
    )

    content: str = Field(
        min_length=0,
        description="The file content loaded from the repository.",
    )

    media_type: str = Field(default="text/plain")

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/").strip()
        if not normalized:
            raise ValueError("path must not be blank")
        return normalized


class RepositoryAccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_root: str = Field(min_length=1)
    selected_files: list[str] = Field(default_factory=list)
    max_file_count: int = Field(default=100, ge=1)
    max_file_content_length: int = Field(default=10_000, ge=0)

    @field_validator("selected_files")
    @classmethod
    def validate_selected_files(cls, value: list[str]) -> list[str]:
        if len(value) > 100:
            raise ValueError("selected_files cannot contain more than 100 file paths")
        if any(not item or not item.strip() for item in value):
            raise ValueError("selected_files must not contain empty file paths")
        return [item.strip() for item in value]


class RepositoryContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_root: str
    files: list[RepositoryFileReference] = Field(default_factory=list)

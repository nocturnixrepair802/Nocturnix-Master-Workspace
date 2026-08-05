from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RepositoryStatusResponse(BaseModel):
    status: str
    root_name: str
    indexed_file_count: int
    ignored_path_count: int
    max_file_bytes: int


class RepositoryFileItem(BaseModel):
    relative_path: str
    extension: str
    size_bytes: int


class RepositoryFilesResponse(BaseModel):
    items: list[RepositoryFileItem]
    total: int
    limit: int
    offset: int


class RepositorySearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=200)
    search_content: bool = True
    extensions: list[str] | None = Field(default=None, max_length=32)
    limit: int = Field(default=25, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def clean_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

    @field_validator("extensions")
    @classmethod
    def clean_extensions(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for extension in value:
            ext = extension.lower().strip()
            if ext and not ext.startswith("."):
                ext = f".{ext}"
            if ext:
                cleaned.append(ext)
        return cleaned or None


class RepositorySearchMatch(BaseModel):
    relative_path: str
    match_type: str
    line_number: int | None = None
    excerpt: str
    order: int


class RepositorySearchResponse(BaseModel):
    query: str
    items: list[RepositorySearchMatch]
    limit: int


class RepositoryFileResponse(BaseModel):
    relative_path: str
    extension: str
    size_bytes: int
    content: str
    truncated: bool

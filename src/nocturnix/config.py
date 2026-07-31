from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOCTURNIX_", env_file=".env", extra="ignore", populate_by_name=True
    )

    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    mock_providers_enabled: bool = True
    external_providers_enabled: bool = False
    openai_enabled: bool = False
    openai_api_key: str = Field(
        default="",
        repr=False,
        validation_alias=AliasChoices("NOCTURNIX_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-5-mini",
        validation_alias=AliasChoices("NOCTURNIX_OPENAI_MODEL", "OPENAI_MODEL"),
    )
    openai_timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    openai_max_tool_rounds: int = Field(default=6, ge=1, le=20)
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:8000", "http://localhost:8000"]
    )
    rate_limit_per_minute: int = Field(default=120, ge=1, le=10_000)
    knowledge_base_path: str = "src/nocturnix/knowledge"
    public_contact_message: str = "Development mock assistant only."
    dev_identity_enabled: bool = True
    database_url: str = "sqlite:///./data/nocturnix_assistant.db"
    database_echo: bool = False
    database_migration_mode: str = "manual"
    data_retention_days: int = Field(default=30, ge=1, le=3650)
    audit_retention_days: int = Field(default=365, ge=1, le=3650)
    conversation_retention_days: int = Field(default=30, ge=1, le=3650)
    repair_intake_retention_days: int = Field(default=90, ge=1, le=3650)
    auth_mode: str = "session"
    allow_development_registration: bool = False
    allow_development_header_auth: bool = False
    allow_development_password_reset_delivery: bool = False
    session_cookie_name: str = "nocturnix_session"
    session_idle_minutes: int = Field(default=30, ge=1, le=1440)
    session_absolute_hours: int = Field(default=12, ge=1, le=720)
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    login_max_attempts: int = Field(default=5, ge=1, le=20)
    login_lockout_minutes: int = Field(default=15, ge=1, le=1440)
    password_reset_minutes: int = Field(default=20, ge=1, le=1440)
    oauth_state_minutes: int = Field(default=10, ge=1, le=120)
    allowed_redirect_uris: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:8000/"])
    secret_storage_enabled: bool = False
    secret_encryption_key: str = ""
    secret_key_version: str = "development-v1"  # noqa: S105
    mock_oauth_enabled: bool = True

    @field_validator("openai_api_key")
    @classmethod
    def clean_openai_api_key(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_database_settings(self) -> "Settings":
        if self.database_migration_mode not in {"manual", "auto-test-only"}:
            raise ValueError("DATABASE_MIGRATION_MODE must be manual or auto-test-only")
        if self.auth_mode not in {"session", "development_header", "disabled"}:
            raise ValueError("AUTH_MODE must be session, development_header, or disabled")
        if self.auth_mode == "development_header" and (
            self.environment != "development" or not self.allow_development_header_auth
        ):
            raise ValueError(
                "development_header auth requires development environment and explicit opt-in"
            )
        if self.session_cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_COOKIE_SAMESITE must be lax, strict, or none")
        if not self.database_url.startswith(("sqlite:///", "sqlite:///:memory:")):
            raise ValueError("only development SQLite DATABASE_URL is enabled in v0.1.4")
        if self.openai_enabled and not self.external_providers_enabled:
            raise ValueError("OPENAI_ENABLED requires EXTERNAL_PROVIDERS_ENABLED")
        if self.openai_enabled and not self.openai_api_key:
            raise ValueError("OPENAI_ENABLED requires OPENAI_API_KEY")
        if self.external_providers_enabled and not self.openai_enabled:
            raise ValueError("EXTERNAL_PROVIDERS_ENABLED currently requires OPENAI_ENABLED")
        return self

    @property
    def safe_knowledge_path(self) -> Path:
        return Path(self.knowledge_base_path)

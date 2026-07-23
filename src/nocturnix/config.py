from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOCTURNIX_", env_file=".env", extra="ignore")

    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    mock_providers_enabled: bool = True
    external_providers_enabled: bool = False
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

    @field_validator("external_providers_enabled")
    @classmethod
    def reject_live_providers(cls, value: bool) -> bool:
        if value:
            raise ValueError("external providers are disabled for development v0.1.3")
        return value

    @model_validator(mode="after")
    def validate_database_settings(self) -> "Settings":
        if self.database_migration_mode not in {"manual", "auto-test-only"}:
            raise ValueError("DATABASE_MIGRATION_MODE must be manual")
        if not self.database_url.startswith(("sqlite:///", "sqlite:///:memory:")):
            raise ValueError("only development SQLite DATABASE_URL is enabled in v0.1.3")
        return self

    @property
    def safe_knowledge_path(self) -> Path:
        return Path(self.knowledge_base_path)

from pathlib import Path

from pydantic import Field, field_validator
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

    @field_validator("external_providers_enabled")
    @classmethod
    def reject_live_providers(cls, value: bool) -> bool:
        if value:
            raise ValueError("external providers are disabled for development v0.1.2")
        return value

    @property
    def safe_knowledge_path(self) -> Path:
        return Path(self.knowledge_base_path)

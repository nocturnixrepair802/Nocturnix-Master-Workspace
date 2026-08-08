from __future__ import annotations

from nocturnix.assistant.mock_provider import MockCodingProvider
from nocturnix.assistant.openai_provider import CodingAssistantProvider, OpenAICodingProvider
from nocturnix.config import Settings


def create_coding_provider(settings: Settings) -> CodingAssistantProvider:
    if settings.coding_provider == "mock":
        return MockCodingProvider()
    if settings.coding_provider == "openai":
        return OpenAICodingProvider(
            settings.openai_api_key,
            settings.openai_model,
            settings.openai_timeout_seconds,
        )
    raise ValueError(f"Unsupported coding provider: {settings.coding_provider}")


def provider_name(provider: CodingAssistantProvider) -> str:
    return str(getattr(provider, "provider", "openai"))


__all__ = ["create_coding_provider", "provider_name"]

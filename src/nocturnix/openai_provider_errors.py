from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpenAIProviderFailure:
    category: str
    status_code: int
    public_detail: str
    retryable: bool
    request_id: str | None = None


_ERROR_TYPES: dict[str, tuple[str, int, str, bool]] = {
    "APITimeoutError": (
        "timeout",
        504,
        "The AI provider timed out. Please try again.",
        True,
    ),
    "APIConnectionError": (
        "connection",
        503,
        "The AI provider is temporarily unreachable. Please try again.",
        True,
    ),
    "RateLimitError": (
        "rate_limit",
        429,
        "The AI provider is temporarily rate limited. Please try again shortly.",
        True,
    ),
    "AuthenticationError": (
        "authentication",
        503,
        "The AI provider credentials are not accepted.",
        False,
    ),
    "PermissionDeniedError": (
        "permission",
        503,
        "The configured AI provider account cannot access this resource.",
        False,
    ),
    "NotFoundError": (
        "resource_not_found",
        503,
        "The configured AI model or provider resource is unavailable.",
        False,
    ),
    "BadRequestError": (
        "bad_request",
        502,
        "The AI provider rejected the request.",
        False,
    ),
    "UnprocessableEntityError": (
        "unprocessable_request",
        502,
        "The AI provider could not process the request.",
        False,
    ),
    "InternalServerError": (
        "provider_internal",
        502,
        "The AI provider encountered a temporary error. Please try again.",
        True,
    ),
    "APIResponseValidationError": (
        "invalid_response",
        502,
        "The AI provider returned an invalid response.",
        True,
    ),
}


def classify_openai_exception(exc: Exception) -> OpenAIProviderFailure | None:
    """Return a safe provider failure without exposing exception text or secrets."""

    error_type = type(exc).__name__
    mapped = _ERROR_TYPES.get(error_type)
    request_id = _request_id(exc)
    if mapped is not None:
        category, status_code, public_detail, retryable = mapped
        return OpenAIProviderFailure(
            category=category,
            status_code=status_code,
            public_detail=public_detail,
            retryable=retryable,
            request_id=request_id,
        )

    provider_status = getattr(exc, "status_code", None)
    if isinstance(provider_status, int):
        if provider_status == 429:
            return OpenAIProviderFailure(
                category="rate_limit",
                status_code=429,
                public_detail=(
                    "The AI provider is temporarily rate limited. "
                    "Please try again shortly."
                ),
                retryable=True,
                request_id=request_id,
            )
        if provider_status >= 500:
            return OpenAIProviderFailure(
                category="provider_internal",
                status_code=502,
                public_detail="The AI provider encountered a temporary error. Please try again.",
                retryable=True,
                request_id=request_id,
            )
        if provider_status in {401, 403, 404}:
            return OpenAIProviderFailure(
                category="provider_configuration",
                status_code=503,
                public_detail="The AI provider configuration is unavailable.",
                retryable=False,
                request_id=request_id,
            )
        if 400 <= provider_status < 500:
            return OpenAIProviderFailure(
                category="provider_request",
                status_code=502,
                public_detail="The AI provider rejected the request.",
                retryable=False,
                request_id=request_id,
            )

    return None


def _request_id(exc: Any) -> str | None:
    value = getattr(exc, "request_id", None)
    if isinstance(value, str) and value:
        return value[:200]
    return None


__all__ = ["OpenAIProviderFailure", "classify_openai_exception"]

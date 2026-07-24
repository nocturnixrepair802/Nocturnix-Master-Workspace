from __future__ import annotations

from nocturnix.openai_provider_errors import classify_openai_exception


class APITimeoutError(Exception):
    pass


class RateLimitError(Exception):
    request_id = "req_rate_limit"


class AuthenticationError(Exception):
    pass


class UnknownError(Exception):
    pass


class GenericStatusError(Exception):
    def __init__(self, status_code: int, request_id: str | None = None) -> None:
        super().__init__("sensitive provider message")
        self.status_code = status_code
        self.request_id = request_id


def test_timeout_is_safe_and_retryable() -> None:
    failure = classify_openai_exception(APITimeoutError("secret timeout details"))

    assert failure is not None
    assert failure.category == "timeout"
    assert failure.status_code == 504
    assert failure.retryable is True
    assert "secret" not in failure.public_detail


def test_rate_limit_preserves_only_safe_request_id() -> None:
    failure = classify_openai_exception(RateLimitError("quota details"))

    assert failure is not None
    assert failure.category == "rate_limit"
    assert failure.status_code == 429
    assert failure.request_id == "req_rate_limit"


def test_authentication_failure_is_not_retryable() -> None:
    failure = classify_openai_exception(AuthenticationError("sk-proj-sensitive"))

    assert failure is not None
    assert failure.category == "authentication"
    assert failure.status_code == 503
    assert failure.retryable is False
    assert "sk-proj" not in failure.public_detail


def test_status_fallback_maps_server_error() -> None:
    failure = classify_openai_exception(GenericStatusError(503, "req_server"))

    assert failure is not None
    assert failure.category == "provider_internal"
    assert failure.status_code == 502
    assert failure.retryable is True
    assert failure.request_id == "req_server"


def test_status_fallback_maps_provider_configuration() -> None:
    failure = classify_openai_exception(GenericStatusError(403))

    assert failure is not None
    assert failure.category == "provider_configuration"
    assert failure.status_code == 503
    assert failure.retryable is False


def test_unknown_programming_error_is_not_masked() -> None:
    assert classify_openai_exception(UnknownError("bug")) is None

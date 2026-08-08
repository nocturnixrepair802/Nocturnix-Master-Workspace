from types import SimpleNamespace

import pytest

from nocturnix.assistant import openai_provider
from nocturnix.assistant.openai_provider import CodingProviderError, OpenAICodingProvider


class Responses:
    def __init__(self, response=None, failure: Exception | None = None) -> None:
        self.response = response
        self.failure = failure
        self.request = None

    def create(self, **request):
        self.request = request
        if self.failure:
            raise self.failure
        return self.response


class Client:
    def __init__(self, responses: Responses) -> None:
        self.responses = responses


def provider(monkeypatch, responses: Responses) -> OpenAICodingProvider:
    monkeypatch.setattr(openai_provider, "OpenAI", lambda **kwargs: Client(responses))
    return OpenAICodingProvider("not-a-real-key", "test-model")


def test_provider_uses_responses_api_and_fixed_instructions(monkeypatch) -> None:
    responses = Responses(SimpleNamespace(output_text="  Useful answer.  "))
    instance = provider(monkeypatch, responses)
    assert instance.answer("Question", "Context") == "Useful answer."
    assert responses.request is not None
    assert responses.request["model"] == "test-model"
    assert responses.request["instructions"] == openai_provider.SYSTEM_INSTRUCTIONS
    assert "Question" in responses.request["input"]


def test_provider_returns_safe_errors(monkeypatch) -> None:
    UnknownProviderError = type("UnknownProviderError", (Exception,), {})
    instance = provider(monkeypatch, Responses(failure=UnknownProviderError("secret detail")))
    with pytest.raises(CodingProviderError, match="provider request failed"):
        instance.answer("Question")

    empty = provider(monkeypatch, Responses(SimpleNamespace(output_text=" ")))
    with pytest.raises(CodingProviderError, match="no text response"):
        empty.answer("Question")

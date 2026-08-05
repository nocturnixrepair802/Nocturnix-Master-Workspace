from nocturnix.assistant.mock_provider import MockCodingProvider


def test_mock_provider_returns_deterministic_output() -> None:
    provider = MockCodingProvider()
    first = provider.answer("Explain AssistantTaskService", "optional context")
    second = provider.answer("Explain AssistantTaskService", "optional context")

    assert first == second
    assert first.startswith("Mock development response")
    assert "Explain AssistantTaskService" in first
    assert "without an external model request" in first
    assert provider.model == "nocturnix-mock"


def test_mock_provider_has_no_openai_dependency(monkeypatch) -> None:
    import nocturnix.assistant.openai_provider as openai_provider

    def fail_openai(**kwargs):
        raise AssertionError("OpenAI must not be constructed in mock mode")

    monkeypatch.setattr(openai_provider, "OpenAI", fail_openai)
    assert "Mock development response" in MockCodingProvider().answer("Hello")

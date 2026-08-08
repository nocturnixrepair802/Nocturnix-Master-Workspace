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


def test_mock_provider_with_repository_context_returns_local_summary() -> None:
    provider = MockCodingProvider()
    context = (
        "File: example.py\n"
        '"""Example module."""\n'
        "import os\n\n"
        "class Example:\n"
        '    """Example class."""\n'
        "    def run(self):\n"
        "        pass\n"
    )

    answer = provider.answer("Summarize this code.", context)

    assert "Attached repository files summary:" in answer
    assert "File: example.py" in answer
    assert "class Example" in answer
    assert "public methods:" in answer
    assert "deterministic and local" in answer


def test_mock_provider_does_not_execute_code() -> None:
    provider = MockCodingProvider()
    context = "File: unsafe.py\nx = 1/0\ndef danger():\n    __import__('os').system('echo safe')\n"

    answer = provider.answer("Check this code.", context)

    assert "Attached repository files summary:" in answer
    assert "File: unsafe.py" in answer
    assert "deterministic and local" in answer
    assert "external model" not in answer.splitlines()[0]


def test_mock_provider_handles_malformed_python_safely() -> None:
    provider = MockCodingProvider()
    context = "File: bad.py\ndef bad(:\n    pass\n"

    answer = provider.answer("Summarize this code.", context)

    assert "File: bad.py" in answer
    assert "Could not parse as Python source" in answer
    assert "deterministic and local" in answer


def test_mock_provider_unsupported_file_type_fallback() -> None:
    provider = MockCodingProvider()
    context = "File: notes.txt\nTitle: Example\nSome plain text here.\n"

    answer = provider.answer("Summarize this file.", context)

    assert "File: notes.txt" in answer
    assert "Line count: 2" in answer
    assert "non-empty lines: 2" in answer


def test_mock_provider_multiple_attached_files_summarize_all() -> None:
    provider = MockCodingProvider()
    context = "File: a.py\ndef alpha():\n    pass\n\nFile: b.md\n# Title\n"

    answer = provider.answer("Summarize these files.", context)

    assert "File: a.py" in answer
    assert "File: b.md" in answer
    assert "Top-level functions:" in answer
    assert "Headings:" in answer


def test_mock_provider_does_not_make_network_calls(monkeypatch) -> None:
    import urllib.request

    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Network call attempted")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    provider = MockCodingProvider()
    context = "File: example.py\ndef safe():\n    return True\n"

    answer = provider.answer("Summarize code safely.", context)

    assert "Attached repository files summary:" in answer
    assert "Network call attempted" not in answer

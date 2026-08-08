from __future__ import annotations

from nocturnix.assistant.local_code_summary import summarize_repository_context_text


def test_summarize_python_module_docstring_and_class_names() -> None:
    context = (
        "File: example.py\n"
        '"""Example module docstring."""\n'
        "import json\n\n"
        "class DemoService:\n"
        '    """Service for demos."""\n'
        "    def start(self):\n"
        "        pass\n\n"
        "def helper():\n"
        "    return True\n"
    )

    summary = summarize_repository_context_text(context)

    assert "File: example.py" in summary
    assert "Module docstring: Example module docstring." in summary
    assert "class DemoService" in summary
    assert "Top-level functions:" in summary
    assert "def helper" not in summary
    assert "helper()" in summary


def test_summarize_multiple_files_in_one_context() -> None:
    context = "File: one.py\ndef alpha():\n    pass\n\nFile: README.md\n# Title\nSummary text\n"

    summary = summarize_repository_context_text(context)

    assert "File: one.py" in summary
    assert "File: README.md" in summary
    assert "Headings:" in summary


def test_summarize_malformed_python_returns_fallback() -> None:
    context = "File: bad.py\ndef bad(:\n    pass\n"

    summary = summarize_repository_context_text(context)

    assert "File: bad.py" in summary
    assert "Could not parse as Python source" in summary


def test_summarize_json_top_level_keys() -> None:
    context = 'File: data.json\n{"foo": 1, "bar": 2}\n'

    summary = summarize_repository_context_text(context)

    assert "File: data.json" in summary
    assert "Top-level keys: bar, foo" in summary


def test_summarize_unsupported_file_type_returns_generic_summary() -> None:
    context = "File: notes.txt\nplain text line\n"

    summary = summarize_repository_context_text(context)

    assert "File: notes.txt" in summary
    assert "Line count: 1" in summary


def test_summarize_is_deterministic() -> None:
    context = "File: stable.py\ndef stable():\n    return True\n"

    first = summarize_repository_context_text(context)
    second = summarize_repository_context_text(context)

    assert first == second

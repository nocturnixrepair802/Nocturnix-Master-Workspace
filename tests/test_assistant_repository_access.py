from __future__ import annotations

from pathlib import Path

from nocturnix.assistant.repository_access import (
    RepositoryAccessError,
    build_repository_context_text,
    load_repository_context,
)
from nocturnix.assistant.repository_models import RepositoryAccessRequest


def test_load_repository_context_reads_selected_files(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file_a = repository_root / "README.md"
    file_a.write_text("Hello world\n", encoding="utf-8")
    file_b = repository_root / "src" / "example.py"
    file_b.parent.mkdir()
    file_b.write_text("print('example')\n", encoding="utf-8")

    request = RepositoryAccessRequest(
        repository_root=str(repository_root),
        selected_files=["README.md", "src/example.py"],
    )

    context = load_repository_context(request)

    assert context.repository_root == str(repository_root.resolve())
    assert len(context.files) == 2
    assert context.files[0].path == "README.md"
    assert context.files[0].content == "Hello world\n"
    assert context.files[1].path == "src/example.py"
    assert "print('example')" in context.files[1].content


def test_build_repository_context_text_formats_files(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    file_path = repository_root / "notes.txt"
    file_path.write_text("Line one\nLine two\n", encoding="utf-8")

    request = RepositoryAccessRequest(
        repository_root=str(repository_root),
        selected_files=["notes.txt"],
    )

    context = load_repository_context(request)
    text = build_repository_context_text(context)

    assert "File: notes.txt" in text
    assert "Line one" in text
    assert "Line two" in text


def test_load_repository_context_rejects_paths_outside_repository(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")

    request = RepositoryAccessRequest(
        repository_root=str(repository_root),
        selected_files=["../outside.txt"],
    )

    try:
        load_repository_context(request)
    except RepositoryAccessError as exc:
        assert "outside repository root" in str(exc)
    else:
        raise AssertionError("Expected RepositoryAccessError for outside path")


def test_load_repository_context_rejects_missing_files(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    request = RepositoryAccessRequest(
        repository_root=str(repository_root),
        selected_files=["missing.txt"],
    )

    try:
        load_repository_context(request)
    except RepositoryAccessError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("Expected RepositoryAccessError for missing file")

from pathlib import Path

from nocturnix.db import ensure_sqlite_parent


def test_ensure_sqlite_parent_creates_relative_missing_parent(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    database_url = "sqlite:///./data/nocturnix_assistant.db"

    ensure_sqlite_parent(database_url)

    assert (tmp_path / "data").is_dir()
    assert not (tmp_path / "data" / "nocturnix_assistant.db").exists()


def test_ensure_sqlite_parent_accepts_existing_parent(tmp_path: Path) -> None:
    parent = tmp_path / "existing"
    parent.mkdir()
    database_file = parent / "assistant.db"

    ensure_sqlite_parent(f"sqlite:///{database_file}")

    assert parent.is_dir()
    assert not database_file.exists()


def test_ensure_sqlite_parent_creates_temporary_absolute_parent(tmp_path: Path) -> None:
    parent = tmp_path / "nested" / "db"
    database_file = parent / "assistant.db"

    ensure_sqlite_parent(f"sqlite:///{database_file}")

    assert parent.is_dir()
    assert not database_file.exists()


def test_ensure_sqlite_parent_ignores_non_sqlite_urls(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    ensure_sqlite_parent("postgresql://user:password@example.test/nocturnix")

    assert list(tmp_path.iterdir()) == []

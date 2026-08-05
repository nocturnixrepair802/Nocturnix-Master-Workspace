from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings


def settings(tmp_path: Path, repo: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "database_url": f"sqlite:///{tmp_path / 'assistant.db'}",
        "database_migration_mode": "auto-test-only",
        "auth_mode": "development_header",
        "allow_development_header_auth": True,
        "coding_provider": "mock",
        "repository_root": str(repo),
        "repository_max_file_bytes": 64,
        "repository_search_result_limit": 10,
    }
    values.update(overrides)
    return Settings(**values)


def headers() -> dict[str, str]:
    return {"X-Nocturnix-Dev-User": "owner-one"}


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "service.py").write_text(
        "class AssistantTaskService:\n    pass\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("Repository guide\n", encoding="utf-8")
    (repo / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")
    (repo / "local.db").write_bytes(b"sqlite")
    (repo / ".git").mkdir()
    (repo / ".git" / "config").write_text("secret", encoding="utf-8")
    (repo / "large.py").write_text("x" * 100, encoding="utf-8")
    return repo


def client_for(tmp_path: Path, repo: Path) -> TestClient:
    return TestClient(create_app(settings(tmp_path, repo)))


def test_repository_status_succeeds_for_authenticated_users(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        response = client.get("/api/assistant/repository/status", headers=headers())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["root_name"] == "repo"
    assert body["indexed_file_count"] == 2
    assert body["ignored_path_count"] >= 3
    assert str(repo) not in response.text


def test_repository_endpoints_require_authentication(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        assert client.get("/api/assistant/repository/status").status_code == 401
        assert client.get("/api/assistant/repository/files").status_code == 401
        assert (
            client.post("/api/assistant/repository/search", json={"query": "service"}).status_code
            == 401
        )
        assert client.get("/api/assistant/repository/file?path=README.md").status_code == 401


def test_file_listing_excludes_ignored_paths_and_filters(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        response = client.get(
            "/api/assistant/repository/files?extension=.py&limit=1",
            headers=headers(),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    paths = [item["path"] for item in body["items"]]
    assert paths == ["src/service.py"]
    assert ".env" not in response.text
    assert "local.db" not in response.text


def test_secret_database_traversal_absolute_and_oversized_reads_rejected(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        unsafe_paths = [
            ".env",
            "local.db",
            "../outside.py",
            str(repo / "src" / "service.py"),
            "large.py",
        ]
        for path in unsafe_paths:
            response = client.get(
                "/api/assistant/repository/file",
                params={"path": path},
                headers=headers(),
            )
            assert response.status_code == 400


def test_symlink_escape_is_rejected_where_supported(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("secret", encoding="utf-8")
    link = repo / "src" / "outside.py"
    try:
        link.symlink_to(outside)
    except OSError:
        return
    with client_for(tmp_path, repo) as client:
        response = client.get(
            "/api/assistant/repository/file",
            params={"path": "src/outside.py"},
            headers=headers(),
        )
    assert response.status_code == 400


def test_safe_source_file_can_be_read(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        response = client.get(
            "/api/assistant/repository/file?path=src/service.py",
            headers=headers(),
        )
    assert response.status_code == 200
    assert response.json()["content"].startswith("class AssistantTaskService")


def test_filename_content_extension_and_limit_search(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        filename = client.post(
            "/api/assistant/repository/search",
            headers=headers(),
            json={"query": "service", "search_content": False, "limit": 1},
        )
        content = client.post(
            "/api/assistant/repository/search",
            headers=headers(),
            json={"query": "AssistantTaskService", "extensions": [".py"], "limit": 5},
        )
    assert filename.status_code == 200
    assert len(filename.json()["items"]) == 1
    assert filename.json()["items"][0]["match_type"] == "filename"
    assert content.status_code == 200
    match = content.json()["items"][0]
    assert match["path"] == "src/service.py"
    assert match["match_type"] == "content"
    assert match["line_number"] == 1
    assert "AssistantTaskService" in match["excerpt"]


def test_selected_files_loaded_into_chat_context_and_persisted(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with client_for(tmp_path, repo) as client:
        response = client.post(
            "/api/assistant/chat",
            headers=headers(),
            json={"message": "Explain it", "selected_files": ["src/service.py"]},
        )
        invalid = client.post(
            "/api/assistant/chat",
            headers=headers(),
            json={"message": "Explain it", "selected_files": [".env"]},
        )
    assert response.status_code == 200
    assert "src/service.py" in response.json()["answer"]
    assert invalid.status_code == 400


def test_no_repository_write_or_network_occurs(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    before = sorted(
        (p.relative_to(repo).as_posix(), p.stat().st_mtime_ns)
        for p in repo.rglob("*")
        if p.is_file()
    )
    with client_for(tmp_path, repo) as client:
        client.get("/api/assistant/repository/files", headers=headers())
        client.post(
            "/api/assistant/repository/search",
            headers=headers(),
            json={"query": "service"},
        )
        client.get("/api/assistant/repository/file?path=src/service.py", headers=headers())
    after = sorted(
        (p.relative_to(repo).as_posix(), p.stat().st_mtime_ns)
        for p in repo.rglob("*")
        if p.is_file()
    )
    assert after == before

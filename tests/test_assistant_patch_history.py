from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.config import Settings


def make_test_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        database_url=(f"sqlite:///{tmp_path / 'assistant.db'}"),
        database_migration_mode="auto-test-only",
        auth_mode="development_header",
        allow_development_header_auth=True,
        coding_provider="mock",
        openai_enabled=False,
        external_providers_enabled=False,
        rate_limit_per_minute=500,
    )


def create_repository(
    tmp_path: Path,
) -> tuple[Path, Path]:
    repository_root = tmp_path / "repository"

    source_file = repository_root / "src" / "nocturnix" / "assistant" / "service.py"

    source_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_file.write_text(
        ("class AssistantTaskService:\n    def create_task(self) -> None:\n        pass\n"),
        encoding="utf-8",
    )

    return repository_root, source_file


def developer_headers(
    user_id: str = "local-developer",
) -> dict[str, str]:
    return {
        "X-Nocturnix-Dev-User": user_id,
    }


def create_persisted_patch(
    client: TestClient,
    repository_root: Path,
) -> dict[str, object]:
    response = client.post(
        "/api/assistant/repository/propose-patch",
        headers=developer_headers(),
        json={
            "instruction": ("Add a class docstring to AssistantTaskService."),
            "selected_files": [
                "src/nocturnix/assistant/service.py",
            ],
            "title": "Document AssistantTaskService",
            "repository_root": str(repository_root),
        },
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["proposal_id"]
    assert payload["task_id"]

    return payload


def test_patch_proposal_response_contains_persisted_ids(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    original_content = source_file.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        payload = create_persisted_patch(
            client,
            repository_root,
        )

    assert isinstance(payload["proposal_id"], str)
    assert payload["proposal_id"]

    assert isinstance(payload["task_id"], str)
    assert payload["task_id"]

    assert source_file.read_text(encoding="utf-8") == original_content


def test_patch_proposal_can_be_retrieved_by_id(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        created = create_persisted_patch(
            client,
            repository_root,
        )

        response = client.get(
            (f"/api/assistant/patches/{created['proposal_id']}"),
            headers=developer_headers(),
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == created["proposal_id"]
    assert payload["task_id"] == created["task_id"]

    assert payload["target_file"] == "src/nocturnix/assistant/service.py"

    assert payload["instructions"] == "Add a class docstring to AssistantTaskService."

    assert payload["unified_diff"]

    assert len(payload["original_sha256"]) == 64
    assert len(payload["proposed_sha256"]) == 64

    assert payload["original_sha256"] != payload["proposed_sha256"]

    metadata = payload["metadata_json"]

    assert metadata["title"] == ("Document AssistantTaskService")
    assert metadata["generated_locally"] is True
    assert metadata["applied"] is False


def test_task_patch_history_lists_persisted_proposal(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        created = create_persisted_patch(
            client,
            repository_root,
        )

        response = client.get(
            (f"/api/assistant/tasks/{created['task_id']}/patches"),
            headers=developer_headers(),
        )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["id"] == created["proposal_id"]
    assert item["task_id"] == created["task_id"]

    assert item["target_file"] == "src/nocturnix/assistant/service.py"


def test_patch_history_persists_across_requests(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        created = create_persisted_patch(
            client,
            repository_root,
        )

        first_response = client.get(
            (f"/api/assistant/patches/{created['proposal_id']}"),
            headers=developer_headers(),
        )

        second_response = client.get(
            (f"/api/assistant/patches/{created['proposal_id']}"),
            headers=developer_headers(),
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json()["id"] == second_response.json()["id"]


def test_patch_proposal_is_not_visible_to_other_owner(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        created = create_persisted_patch(
            client,
            repository_root,
        )

        response = client.get(
            (f"/api/assistant/patches/{created['proposal_id']}"),
            headers=developer_headers("different-developer"),
        )

    assert response.status_code == 404


def test_task_patch_history_is_not_visible_to_other_owner(
    tmp_path: Path,
) -> None:
    repository_root, _ = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        created = create_persisted_patch(
            client,
            repository_root,
        )

        response = client.get(
            (f"/api/assistant/tasks/{created['task_id']}/patches"),
            headers=developer_headers("different-developer"),
        )

    assert response.status_code == 404


def test_missing_patch_proposal_returns_404(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get(
            "/api/assistant/patches/missing-proposal",
            headers=developer_headers(),
        )

    assert response.status_code == 404

    assert response.json()["detail"] == "Patch proposal not found."


def test_patch_history_endpoint_requires_authentication(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.get("/api/assistant/patches/missing-proposal")

    assert response.status_code == 401

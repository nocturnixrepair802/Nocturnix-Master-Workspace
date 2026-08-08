from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.assistant.patch_apply import (
    PatchApplyService,
)
from nocturnix.config import Settings

FIRST_FILE = "src/nocturnix/assistant/first_service.py"

SECOND_FILE = "src/nocturnix/assistant/second_service.py"

ORIGINAL_CONTENT = "class AssistantTaskService:\n    def create_task(self) -> None:\n        pass\n"


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


def developer_headers(
    user_id: str = "local-developer",
) -> dict[str, str]:
    return {
        "X-Nocturnix-Dev-User": user_id,
    }


def create_multi_file_repository(
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    repository_root = tmp_path / "repository"

    first_path = repository_root / FIRST_FILE

    second_path = repository_root / SECOND_FILE

    first_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    first_path.write_text(
        ORIGINAL_CONTENT,
        encoding="utf-8",
    )

    second_path.write_text(
        ORIGINAL_CONTENT,
        encoding="utf-8",
    )

    return (
        repository_root,
        first_path,
        second_path,
    )


def create_multi_file_proposal(
    client: TestClient,
    repository_root: Path,
) -> dict[str, Any]:
    response = client.post(
        "/api/assistant/repository/propose-patch",
        headers=developer_headers(),
        json={
            "instruction": ("Add a class docstring to AssistantTaskService."),
            "selected_files": [
                FIRST_FILE,
                SECOND_FILE,
            ],
            "title": ("Document AssistantTaskService"),
            "repository_root": str(repository_root),
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def apply_proposal(
    client: TestClient,
    proposal_id: object,
):
    return client.post(
        (f"/api/assistant/patches/{proposal_id}/apply"),
        headers=developer_headers(),
        json={
            "confirm": True,
        },
    )


def test_multi_file_proposal_response_contains_all_files(
    tmp_path: Path,
) -> None:
    (
        repository_root,
        _,
        _,
    ) = create_multi_file_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

    assert proposal["affected_files"] == [
        FIRST_FILE,
        SECOND_FILE,
    ]

    assert len(proposal["files"]) == 2

    assert [item["path"] for item in proposal["files"]] == [
        FIRST_FILE,
        SECOND_FILE,
    ]

    for item in proposal["files"]:
        assert item["unified_diff"]
        assert len(item["original_sha256"]) == 64
        assert len(item["proposed_sha256"]) == 64


def test_multi_file_patch_history_returns_all_files(
    tmp_path: Path,
) -> None:
    (
        repository_root,
        _,
        _,
    ) = create_multi_file_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

        response = client.get(
            (f"/api/assistant/patches/{proposal['proposal_id']}"),
            headers=developer_headers(),
        )

    assert response.status_code == 200, response.text

    body = response.json()

    assert len(body["files"]) == 2

    assert [item["path"] for item in body["files"]] == [
        FIRST_FILE,
        SECOND_FILE,
    ]


def test_task_patch_history_returns_all_files(
    tmp_path: Path,
) -> None:
    (
        repository_root,
        _,
        _,
    ) = create_multi_file_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

        response = client.get(
            (f"/api/assistant/tasks/{proposal['task_id']}/patches"),
            headers=developer_headers(),
        )

    assert response.status_code == 200, response.text

    body = response.json()

    assert len(body["items"]) == 1
    assert len(body["items"][0]["files"]) == 2

    assert [item["path"] for item in body["items"][0]["files"]] == [
        FIRST_FILE,
        SECOND_FILE,
    ]


def test_multi_file_patch_apply_updates_all_files(
    tmp_path: Path,
) -> None:
    (
        repository_root,
        first_path,
        second_path,
    ) = create_multi_file_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

        response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

    assert response.status_code == 200, response.text

    expected_docstring = '"""Coordinate AssistantTaskService behavior."""'

    assert expected_docstring in (first_path.read_text(encoding="utf-8"))

    assert expected_docstring in (second_path.read_text(encoding="utf-8"))

    assert response.json()["status"] == ("applied")


def test_multi_file_patch_rejects_stale_second_file_before_any_write(
    tmp_path: Path,
) -> None:
    (
        repository_root,
        first_path,
        second_path,
    ) = create_multi_file_repository(tmp_path)

    original_first = first_path.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

        stale_second = second_path.read_text(encoding="utf-8") + "# external change\n"

        second_path.write_text(
            stale_second,
            encoding="utf-8",
        )

        response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "The target file changed after the patch proposal was generated."
    )

    assert first_path.read_text(encoding="utf-8") == original_first

    assert second_path.read_text(encoding="utf-8") == stale_second


def test_multi_file_patch_rolls_back_first_file_when_second_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        repository_root,
        first_path,
        second_path,
    ) = create_multi_file_repository(tmp_path)

    original_first = first_path.read_text(encoding="utf-8")

    original_second = second_path.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    original_atomic_write = PatchApplyService._atomic_write

    failed_second_write = False

    def failing_atomic_write(
        target_path: Path,
        content: str,
    ) -> None:
        nonlocal failed_second_write

        if target_path == second_path and not failed_second_write:
            failed_second_write = True

            raise OSError("simulated second file write failure")

        original_atomic_write(
            target_path,
            content,
        )

    monkeypatch.setattr(
        PatchApplyService,
        "_atomic_write",
        staticmethod(failing_atomic_write),
    )

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

        response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

    assert response.status_code == 409

    assert first_path.read_text(encoding="utf-8") == original_first

    assert second_path.read_text(encoding="utf-8") == original_second


def test_multi_file_patch_failure_marks_proposal_failed(
    tmp_path: Path,
) -> None:
    (
        repository_root,
        _,
        second_path,
    ) = create_multi_file_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_multi_file_proposal(
            client,
            repository_root,
        )

        second_path.write_text(
            (second_path.read_text(encoding="utf-8") + "# stale\n"),
            encoding="utf-8",
        )

        apply_response = apply_proposal(
            client,
            proposal["proposal_id"],
        )

        assert apply_response.status_code == 409

        history_response = client.get(
            (f"/api/assistant/patches/{proposal['proposal_id']}"),
            headers=developer_headers(),
        )

    assert history_response.status_code == 200

    history = history_response.json()

    assert history["status"] == "failed"
    assert history["failure_reason"]

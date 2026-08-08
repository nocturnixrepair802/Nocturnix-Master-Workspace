from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nocturnix import create_app
from nocturnix.assistant.patch_apply import (
    PatchApplyError,
    PatchApplyService,
)
from nocturnix.config import Settings

TARGET_FILE = "src/nocturnix/assistant/service.py"


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


def create_patch_proposal(
    client: TestClient,
    repository_root: Path,
    *,
    user_id: str = "local-developer",
) -> dict[str, object]:
    response = client.post(
        "/api/assistant/repository/propose-patch",
        headers=developer_headers(user_id),
        json={
            "instruction": ("Add a class docstring to AssistantTaskService."),
            "selected_files": [
                TARGET_FILE,
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


def apply_patch(
    client: TestClient,
    proposal_id: object,
    *,
    user_id: str = "local-developer",
    confirm: bool = True,
):
    return client.post(
        f"/api/assistant/patches/{proposal_id}/apply",
        headers=developer_headers(user_id),
        json={
            "confirm": confirm,
        },
    )


def test_patch_apply_successfully_updates_file(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    original_content = source_file.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        response = apply_patch(
            client,
            proposal["proposal_id"],
        )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["proposal_id"] == (proposal["proposal_id"])
    assert payload["task_id"] == proposal["task_id"]
    assert payload["status"] == "applied"
    assert payload["target_file"] == TARGET_FILE
    assert payload["applied_at"] is not None
    assert payload["applied_by_user_id"] == "local-developer"
    assert payload["failure_reason"] is None

    updated_content = source_file.read_text(encoding="utf-8")

    assert updated_content != original_content

    assert '"""Coordinate AssistantTaskService behavior."""' in updated_content


def test_patch_apply_requires_explicit_confirmation(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    original_content = source_file.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        response = apply_patch(
            client,
            proposal["proposal_id"],
            confirm=False,
        )

    assert response.status_code == 400

    assert response.json()["detail"] == ("Patch application requires explicit confirmation.")

    assert source_file.read_text(encoding="utf-8") == original_content


def test_patch_apply_rejects_second_application(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        first_response = apply_patch(
            client,
            proposal["proposal_id"],
        )

        assert first_response.status_code == 200

        content_after_first_apply = source_file.read_text(encoding="utf-8")

        second_response = apply_patch(
            client,
            proposal["proposal_id"],
        )

    assert second_response.status_code == 409

    assert "cannot be applied" in (second_response.json()["detail"])

    assert "applied" in (second_response.json()["detail"])

    assert source_file.read_text(encoding="utf-8") == content_after_first_apply


def test_patch_apply_rejects_stale_proposal(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        changed_content = source_file.read_text(encoding="utf-8") + "\n# changed after proposal\n"

        source_file.write_text(
            changed_content,
            encoding="utf-8",
        )

        response = apply_patch(
            client,
            proposal["proposal_id"],
        )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "The target file changed after the patch proposal was generated."
    )

    assert source_file.read_text(encoding="utf-8") == changed_content


def test_stale_patch_is_marked_failed(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        source_file.write_text(
            (source_file.read_text(encoding="utf-8") + "# external edit\n"),
            encoding="utf-8",
        )

        first_response = apply_patch(
            client,
            proposal["proposal_id"],
        )

        assert first_response.status_code == 409

        second_response = apply_patch(
            client,
            proposal["proposal_id"],
        )

    assert second_response.status_code == 409

    detail = second_response.json()["detail"]

    assert "cannot be applied" in detail
    assert "failed" in detail


def test_failed_patch_does_not_overwrite_current_file(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        changed_content = (
            'class AssistantTaskService:\n    """External modification."""\n    pass\n'
        )

        source_file.write_text(
            changed_content,
            encoding="utf-8",
        )

        response = apply_patch(
            client,
            proposal["proposal_id"],
        )

    assert response.status_code == 409

    assert source_file.read_text(encoding="utf-8") == changed_content


def test_missing_patch_proposal_returns_404(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = apply_patch(
            client,
            "missing-proposal",
        )

    assert response.status_code == 404

    assert response.json()["detail"] == ("Patch proposal not found.")


def test_other_owner_cannot_apply_patch(
    tmp_path: Path,
) -> None:
    repository_root, source_file = create_repository(tmp_path)

    original_content = source_file.read_text(encoding="utf-8")

    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        proposal = create_patch_proposal(
            client,
            repository_root,
        )

        response = apply_patch(
            client,
            proposal["proposal_id"],
            user_id="different-developer",
        )

    assert response.status_code == 404

    assert source_file.read_text(encoding="utf-8") == original_content


def test_patch_apply_requires_authentication(
    tmp_path: Path,
) -> None:
    app = create_app(make_test_settings(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/assistant/patches/missing/apply",
            json={
                "confirm": True,
            },
        )

    assert response.status_code == 401


def test_apply_unified_diff_rejects_incomplete_diff() -> None:
    with pytest.raises(
        PatchApplyError,
        match="incomplete",
    ):
        PatchApplyService._apply_unified_diff(
            "line one\n",
            "--- a/file.py\n+++ b/file.py",
        )


def test_apply_unified_diff_rejects_missing_hunk() -> None:
    with pytest.raises(
        PatchApplyError,
        match="no patch hunks",
    ):
        PatchApplyService._apply_unified_diff(
            "line one\n",
            ("--- a/file.py\n+++ b/file.py\nnot-a-hunk"),
        )


def test_apply_unified_diff_rejects_invalid_hunk_header() -> None:
    with pytest.raises(
        PatchApplyError,
        match="invalid hunk header",
    ):
        PatchApplyService._apply_unified_diff(
            "line one\n",
            ("--- a/file.py\n+++ b/file.py\n@@ broken @@\n line one"),
        )


def test_apply_unified_diff_rejects_bad_context() -> None:
    with pytest.raises(
        PatchApplyError,
        match="context does not match",
    ):
        PatchApplyService._apply_unified_diff(
            "actual line\n",
            ("--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n expected line"),
        )


def test_apply_unified_diff_rejects_bad_removal() -> None:
    with pytest.raises(
        PatchApplyError,
        match="removal does not match",
    ):
        PatchApplyService._apply_unified_diff(
            "actual line\n",
            ("--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-expected line\n+replacement line"),
        )


def test_apply_unified_diff_rejects_reference_past_eof() -> None:
    with pytest.raises(
        PatchApplyError,
        match="beyond the end",
    ):
        PatchApplyService._apply_unified_diff(
            "only line\n",
            ("--- a/file.py\n+++ b/file.py\n@@ -2,1 +2,1 @@\n-missing line\n+replacement"),
        )
